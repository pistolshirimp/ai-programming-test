import pytest
from your_module import load_scores  # 실제 모듈명으로 변경하세요


@pytest.fixture
def make_csv(tmp_path):
    """테스트용 CSV 파일을 생성하는 헬퍼 픽스처"""
    def _make_csv(content: str, encoding: str = "utf-8"):
        file_path = tmp_path / "scores.csv"
        file_path.write_text(content, encoding=encoding)
        return file_path
    return _make_csv


# ==========================================
# 1. 정상 케이스 (Normal Cases)
# ==========================================

def test_load_scores_normal(make_csv):
    """일반적인 유효 데이터 처리 검증"""
    content = (
        "이름,점수\n"
        "홍길동,85\n"
        "김철수,92\n"
        "이영희,70\n"
    )
    path = make_csv(content)
    kept, skipped = load_scores(path)

    assert kept == [("홍길동", 85), ("김철수", 92), ("이영희", 70)]
    assert skipped == []


def test_load_scores_with_whitespace_and_empty_lines(make_csv):
    """앞뒤 공백 제거(strip) 및 빈 줄 무시 검증"""
    content = (
        "이름,점수\n"
        "\n"
        "  홍길동  ,  85  \n"
        "\n"
        "김철수, 90\n"
    )
    path = make_csv(content)
    kept, skipped = load_scores(path)

    assert kept == [("홍길동", 85), ("김철수", 90)]
    assert skipped == []


def test_load_scores_utf8_bom(make_csv):
    """UTF-8 BOM 인코딩 파일 정상 파싱 검증"""
    content = "이름,점수\n박민수,88\n"
    path = make_csv(content, encoding="utf-8-sig")
    kept, skipped = load_scores(path)

    assert kept == [("박민수", 88)]
    assert skipped == []


def test_load_scores_only_header_or_empty_file(make_csv):
    """헤더만 있는 파일 및 완전히 빈 파일 처리 검증"""
    header_only = make_csv("이름,점수\n")
    assert load_scores(header_only) == ([], [])

    empty_file = make_csv("")
    assert load_scores(empty_file) == ([], [])


# ==========================================
# 2. 경계값 케이스 (Boundary Cases)
# ==========================================

@pytest.mark.parametrize("score_str, expected_score, is_valid", [
    ("-1", None, False),   # 하한선 바로 아래 (무효)
    ("0", 0, True),        # 하한선 경계값 (유효)
    ("1", 1, True),        # 하한선 바로 위 (유효)
    ("99", 99, True),      # 상한선 바로 아래 (유효)
    ("100", 100, True),    # 상한선 경계값 (유효)
    ("101", None, False),  # 상한선 바로 위 (무효)
])
def test_load_scores_boundaries(make_csv, score_str, expected_score, is_valid):
    """점수 허용 범위(0~100)의 경계값 테스트"""
    content = f"이름,점수\n테스터,{score_str}\n"
    path = make_csv(content)
    kept, skipped = load_scores(path)

    if is_valid:
        assert kept == [("테스터", expected_score)]
        assert skipped == []
    else:
        assert kept == []
        assert skipped == [(2, f"테스터,{score_str}", "점수가 0~100 밖")]


# ==========================================
# 3. 예외 및 오류 데이터 케이스 (Exception / Invalid Cases)
# ==========================================

def test_load_scores_file_not_found(tmp_path):
    """존재하지 않는 파일 경로 입력 시 FileNotFoundError 발생 검증"""
    non_existent = tmp_path / "no_such_file.csv"
    with pytest.raises(FileNotFoundError):
        load_scores(non_existent)


@pytest.mark.parametrize("row_str, expected_reason", [
    ("홍길동", "열 개수가 2가 아님"),              # 열 1개
    ("홍길동,80,추가열", "열 개수가 2가 아님"),     # 열 3개
    (",80", "이름이 비어 있음"),                   # 이름 빈 문자열
    ("   ,80", "이름이 비어 있음"),                # 이름 공백만 존재
    ("홍길동,", "점수가 비어 있음"),               # 점수 빈 문자열
    ("홍길동,   ", "점수가 비어 있음"),            # 점수 공백만 존재
    ("홍길동,abc", "점수가 정수가 아님"),          # 문자열 점수
    ("홍길동,85.5", "점수가 정수가 아님"),         # 실수(float) 점수
    ("홍길동,-5", "점수가 0~100 밖"),              # 음수 점수
    ("홍길동,150", "점수가 0~100 밖"),             # 100 초과 점수
])
def test_load_scores_invalid_rows(make_csv, row_str, expected_reason):
    """유효하지 않은 각 행이 정확한 줄 번호, 원본 문자열, 사유와 함께 skipped에 기록되는지 검증"""
    content = f"이름,점수\n{row_str}\n"
    path = make_csv(content)
    kept, skipped = load_scores(path)

    assert kept == []
    assert skipped == [(2, row_str, expected_reason)]


def test_load_scores_mixed_lines_line_numbers(make_csv):
    """정상 줄, 빈 줄, 오류 줄이 섞여 있을 때 정확한 줄 번호(line_no) 추적 검증"""
    content = (
        "이름,점수\n"          # 1번 줄: 헤더
        "정상1,100\n"          # 2번 줄: 유효
        "\n"                   # 3번 줄: 빈 줄 (기록 안 됨)
        "오류열\n"             # 4번 줄: 열 개수 오류
        "  ,50\n"              # 5번 줄: 이름 공백
        "정상2,0\n"            # 6번 줄: 유효
        "오류점수,99.9\n"      # 7번 줄: 정수 아님
    )
    path = make_csv(content)
    kept, skipped = load_scores(path)

    assert kept == [("정상1", 100), ("정상2", 0)]
    assert skipped == [
        (4, "오류열", "열 개수가 2가 아님"),
        (5, "  ,50", "이름이 비어 있음"),
        (7, "오류점수,99.9", "점수가 정수가 아님"),
    ]
