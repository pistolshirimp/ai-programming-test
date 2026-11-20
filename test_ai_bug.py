import pytest

# 테스트 대상 함수
def find_max(scores):
    biggest = scores[0]
    for i in range(1, len(scores) - 1):
        if scores[i] > biggest:
            biggest = scores[i]
    return biggest


# ==========================================
# 1. 정상 케이스 (Normal Cases)
# ==========================================
def test_find_max_normal():
    assert find_max([10, 50, 30, 20]) == 50

def test_find_max_negative_numbers():
    assert find_max([-10, -3, -25, -7]) == -3

def test_find_max_mixed_numbers():
    assert find_max([-5, 0, 12, -2, 8]) == 12

def test_find_max_floats():
    assert find_max([1.5, 3.7, 2.1, 3.69]) == 3.7


# ==========================================
# 2. 경계값 케이스 (Boundary Cases)
# ==========================================
def test_find_max_single_element():
    """요소가 1개뿐인 리스트"""
    assert find_max([42]) == 42

def test_find_max_two_elements():
    """요소가 2개뿐인 리스트 (두 번째 요소가 큰 경우 현재 로직에서는 실패함)"""
    assert find_max([10, 20]) == 20

def test_find_max_at_first_index():
    """최댓값이 첫 번째 인덱스에 위치한 경우"""
    assert find_max([99, 10, 20, 30]) == 99

def test_find_max_at_last_index():
    """최댓값이 마지막 인덱스에 위치한 경우 (현재 range 버그로 인해 실패함)"""
    assert find_max([10, 20, 30, 99]) == 99

def test_find_max_all_equal():
    """모든 요소가 동일한 값인 경우"""
    assert find_max([7, 7, 7, 7]) == 7

def test_find_max_duplicate_max():
    """최댓값이 중복으로 존재하는 경우"""
    assert find_max([5, 20, 10, 20, 3]) == 20


# ==========================================
# 3. 예외 케이스 (Exception Cases)
# ==========================================
def test_find_max_empty_list():
    """빈 리스트 입력 시 IndexError 발생"""
    with pytest.raises(IndexError):
        find_max([])

def test_find_max_none_input():
    """None 입력 시 TypeError 발생"""
    with pytest.raises(TypeError):
        find_max(None)

def test_find_max_incomparable_types():
    """숫자와 문자열 등 비교 불가능한 타입 혼합 시 TypeError 발생"""
    with pytest.raises(TypeError):
        find_max([10, "20", 30])