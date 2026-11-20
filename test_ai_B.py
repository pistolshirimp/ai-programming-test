import pytest

# 테스트 대상 함수 임포트 (실제 모듈명에 맞게 수정하세요)
from score_loader import load_scores


@pytest.fixture
def create_csv(tmp_path):
    """임시 CSV 파일을 생성하고 경로를 반환하는 헬퍼 픽스처"""
    def _create(content: str, filename: str = "scores.csv"):
        file_path = tmp_path / filename
        file_path.write_text(content, encoding="utf-8")
        return file_path
    return _create


# ---------------------------------------------------------
# 1. 정상 동작 및 기본 케이스
# ---------------------------------------------------------
def test_load_scores_normal_and_boundary_values(create_csv):
    """정상 데이터와 점수 경계값(0, 100), 공백 제거(strip) 동작 검증"""
    content = (
        "name,score\n"
        "홍길동,85\n"
        "김철수,0\n"       # 경계값: 최소 점수 (0)
        "이영희,100\n"     # 경계값: 최대 점수 (100)
        " 박민수 , 92 \n"  # 이름/점수 앞뒤 공백 포함 케이스
    )
    path = create_csv(content)
    kept, skipped = load_scores(path)

    assert kept == [
        ("홍길동", 85),
        ("김철수", 0),
        ("이영희", 100),
        ("박민수", 92),
    ]
    assert skipped == []


def test_duplicate_names_are_kept(create_csv):
    """조건 ⑦: 동명이인이 있을 경우 덮어쓰지 않고 모두 kept에 유지"""
    content = (
        "name,score\n"
        "김민준,70\n"
        "김민준,95\n"
    )
    path = create_csv(content)
    kept, skipped = load_scores(path)

    assert kept == [
        ("김민준", 70),
        ("김민준", 95),
    ]
    assert skipped == []


def test_header_only_returns_empty_lists(create_csv):
    """조건 ②: 헤더만 존재하는 파일은 ([], []) 반환"""
    path = create_csv("name,score\n")
    kept, skipped = load_scores(path)

    assert kept == []
    assert skipped == []


def test_empty_lines_are_ignored_without_recording(create_csv):
    """조건 ⑧: 빈 줄이나 공백만 있는 줄은 skipped에 기록하지 않고 건너뜀 (줄번호 유지 확인)"""
    content = (
        "name,score\n"
        "\n"
        "   \n"
        "홍길동,80\n"
        "\n"
        "이영희,-5\n"  # 6번째 줄 (빈 줄 포함 줄번호 계산 검증)
    )
    path = create_csv(content)
    kept, skipped = load_scores(path)

    assert kept == [("홍길동", 80)]
    assert len(skipped) == 1
    assert skipped[0][0] == 6
    assert skipped[0][1].strip() == "이영희,-5"


# ---------------------------------------------------------
# 2. 예외 발생 케이스
# ---------------------------------------------------------
def test_file_not_found_raises_error(tmp_path):
    """조건 ①: 존재하지 않는 파일 경로 전달 시 FileNotFoundError 발생"""
    non_existent_path = tmp_path / "does_not_exist.csv"

    with pytest.raises(FileNotFoundError):
        load_scores(non_existent_path)


# ---------------------------------------------------------
# 3. 건너뛰기(skipped) 및 경계값 검증 (parametrize 활용)
# ---------------------------------------------------------
@pytest.mark.parametrize(
    "invalid_line, test_desc",
    [
        # 조건 ③: 열 개수가 2가 아님
        ("홍길동", "열 개수 부족 (1개)"),
        ("홍길동,80,A학점", "열 개수 초과 (3개)"),
        ("홍길동,80,", "후행 쉼표로 인한 열 개수 초과 (3개)"),

        # 조건 ④: 점수가 비었거나 정수가 아님
        ("홍길동,", "점수 비어있음"),
        ("홍길동,   ", "점수가 공백만 있음"),
        ("홍길동,85.5", "점수가 실수(float)"),
        ("홍길동,팔십", "점수가 문자열"),
        ("홍길동,NaN", "점수가 NaN"),

        # 조건 ⑤: 점수가 0~100 범위 밖 (경계값: -1, 101)
        ("홍길동,-1", "경계값 미만 (-1)"),
        ("홍길동,101", "경계값 초과 (101)"),
        ("홍길동,-100", "음수 점수"),
        ("홍길동,999", "큰 양수 점수"),

        # 조건 ⑥: 이름이 비었음
        (",85", "이름 비어있음"),
        ("   ,85", "이름이 공백만 있음"),
    ],
)
def test_skipped_rows_conditions(create_csv, invalid_line, test_desc):
    """조건 ③, ④, ⑤, ⑥에 해당하는 잘못된 줄이 skipped에 정확히 기록되는지 검증"""
    content = f"name,score\n{invalid_line}\n"
    path = create_csv(content)

    kept, skipped = load_scores(path)

    assert kept == [], f"실패 케이스({test_desc}): kept는 비어있어야 합니다."
    assert len(skipped) == 1, f"실패 케이스({test_desc}): skipped에 1건이 기록되어야 합니다."

    line_no, raw_line, reason = skipped[0]