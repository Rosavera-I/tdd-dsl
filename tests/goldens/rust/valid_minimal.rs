use calculator::*;

// Source: tests/fixtures/valid_minimal.tdd:10
#[test]
fn test_adds_two_numbers() {
    // Input: {'a': 2, 'b': 3}
    let input = vec![("a", 2), ("b", 3)].into_iter().collect::<std::collections::HashMap<_, _>>();
    let result = add(&input);
    assert_eq!(5, result);
}
