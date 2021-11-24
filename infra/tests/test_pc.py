import pytest
import infra.pc as pc


def test_epsilon_parser():
    subject = pc.epsilon_parser

    actual = subject("abc")
    assert actual.match == ()
    assert actual.next_token_index == 0


def test_empty_parser():
    subject = pc.empty_parser

    with pytest.raises(pc.NoMatchException):
        subject("")


def test_end_of_input_parser():
    subject = pc.end_of_input_parser

    input = "test_input"
    actual = subject(input, index=len(input))
    assert actual.is_empty_output()
    assert actual.next_token_index == len(input)

    with pytest.raises(pc.NoMatchException):
        subject(input, index=0)


def test_any_parser():
    subject = pc.any_parser

    input = "test_input"
    for i in range(0, len(input)):
        actual = subject(input, index=i)
        assert actual.match == input[i]

    with pytest.raises(pc.NoMatchException):
        subject(input, len(input))


def test_make_const():
    test_pred = lambda t: type(t) == int
    subject = pc.make_const(test_pred)

    expected_match = 0
    tokens = ["test_token", expected_match]

    with pytest.raises(pc.NoMatchException):
        subject(tokens)

    actual = subject(tokens, index=1)
    assert actual.match == expected_match
    assert actual.next_token_index == 2

    with pytest.raises(pc.NoMatchException):
        subject(tokens, len(tokens))


def test_make_char():
    test_char = 't'
    subject = pc.make_char(test_char)

    tokens = f'{test_char}_'

    actual = subject(tokens)
    assert actual.match == test_char
    assert actual.next_token_index == 1

    with pytest.raises(pc.NoMatchException):
        subject(tokens, index=1)


def test_make_char_ci():
    test_char = 't'
    subject = pc.make_char_ci(test_char)

    expected_uppercase = 'T'
    tokens = f'{test_char}{expected_uppercase}_'

    actual = subject(tokens)
    assert actual.match == test_char
    assert actual.next_token_index == 1

    actual_upper_case = subject(tokens, index=1)
    assert actual_upper_case.match == expected_uppercase
    assert actual_upper_case.next_token_index == 2

    with pytest.raises(pc.NoMatchException):
        subject(tokens, index=2)


def test_make_word():
    test_word = "test"
    subject = pc.make_word(test_word)

    actual = subject(f"{test_word}not_match")
    assert actual.next_token_index == len(test_word)
    assert actual.match == tuple(test_word)


def test_make_oneof():
    test_chars = "abcdefg"
    subject = pc.make_oneof(test_chars)

    actual = subject(test_chars)
    assert actual.next_token_index == 1
    assert actual.match == test_chars[0]

    with pytest.raises(pc.NoMatchException):
        subject("h")


def test_make_char_range():
    test_range_start = 'a'
    test_range_end = 'c'
    subject = pc.make_char_range(test_range_start, test_range_end)

    token = 'a'
    actual = subject(token)
    assert actual.match == token

    token = 'b'
    actual = subject(token)
    assert actual.match == token

    token = 'c'
    actual = subject(token)
    assert actual.match == token

    with pytest.raises(pc.NoMatchException):
        subject('d')


def test_make_char_range_ci():
    test_range_start = 'a'
    test_range_end = 'C'
    subject = pc.make_char_range_ci(test_range_start, test_range_end)

    token = 'A'
    actual = subject(token)
    assert actual.match == token

    token = 'B'
    actual = subject(token)
    assert actual.match == token

    token = 'C'
    actual = subject(token)
    assert actual.match == token

    with pytest.raises(pc.NoMatchException):
        subject('D')


def test_caten():
    first_token = 'test_token_1'
    head = pc.make_const(lambda t: t == first_token)
    second_token = 'test_token_2'
    tail = pc.make_const(lambda t: t == second_token)
    subject = pc.caten(head, tail)

    actual = subject([first_token, second_token])
    assert actual.match == (first_token, second_token)
    assert actual.next_token_index == 2


def test_caten_list():
    tokens = [f'{i}' for i in range(10)]
    parsers = [pc.make_char(c) for c in tokens]

    subject = pc.caten_list(parsers)

    actual = subject(tokens)
    assert actual.match == tuple(tokens)

    actual = subject("".join(tokens))
    assert actual.match == tuple(tokens)

    with pytest.raises(pc.NoMatchException):
        subject(tokens[:-1])

    with pytest.raises(pc.NoMatchException):
        subject(tokens, index=1)


def test_pack():
    parser = pc.make_char('c')
    expected = 'expected'
    transformation = lambda _: expected

    subject = pc.pack(parser, transformation)

    actual = subject('abc', index=2)
    assert actual.match == expected

    with pytest.raises(pc.NoMatchException):
        subject('not_matched')


def test_disj():
    token_1 = 1
    token_2 = 2
    parser_1 = pc.make_const(lambda t: t == token_1)
    parser_2 = pc.make_const(lambda t: t == token_2)

    subject = pc.disj(parser_1, parser_2)
    actual = subject([1, 2, 3])

    assert actual.match == token_1
    assert actual.next_token_index == 1

    actual = subject([1, 2, 3], index=1)
    assert actual.match == token_2
    assert actual.next_token_index == 2

    with pytest.raises(pc.NoMatchException):
        subject([1, 2, 3], index=2)

    subject_with_epsilon = pc.disj(pc.epsilon_parser, parser_2)
    actual = subject_with_epsilon([2], index=0)

    assert actual.match == pc.EPSILON

    subject_with_empty = pc.disj(pc.empty_parser, parser_2)
    actual = subject_with_empty([2], index=0)

    assert actual.match == 2


def test_disj_list():
    tokens = list(range(10))

    def make_pred(token):
        return lambda t: t == token

    parsers = [pc.make_const(make_pred(token)) for token in tokens]

    subject = pc.disj_list(parsers)

    for token in tokens:
        actual = subject([token])
        assert actual.match == token
        assert actual.next_token_index == 1

    with pytest.raises(pc.NoMatchException):
        subject([10])


def test_star():
    parser = pc.make_char_range_ci('a', 'z')

    subject = pc.star(parser)
    input = 'ABCDEefghijj'
    actual = subject(input)
    assert actual.match == list(input)
    assert actual.next_token_index == len(input)

    actual = subject('')
    assert actual.match == []
    assert actual.next_token_index == 0


def test_plus():
    parser = pc.make_char_range('a', 'z')

    subject = pc.plus(parser)

    match_tokens = 'abcd'
    actual = subject(match_tokens + 'EF')
    assert actual.match == list(match_tokens)
    assert actual.next_token_index == len(match_tokens)

    actual = subject('z')
    assert actual.match == ['z']
    assert actual.next_token_index == 1

    with pytest.raises(pc.NoMatchException):
        subject('')


def test_delayed():
    a_parser = pc.make_char('a')
    subject = pc.disj(pc.caten(a_parser, pc.delayed(lambda: subject)), pc.epsilon_parser)

    actual = subject('aa')
    assert actual.match == ('a', ('a', ()))

    actual = subject('')
    assert actual.match == ()


def test_guard():
    a_parser = pc.make_char('a')
    subject = pc.guard(pc.star(a_parser), lambda match: len(match) > 1)

    with pytest.raises(pc.NoMatchException):
        subject('a')

    actual = subject('aa')
    assert actual.match == ['a', 'a']


def test_diff():
    a_star_parser = pc.star(pc.make_char('a'))
    aa_parser = pc.caten(pc.make_word('aa'), pc.end_of_input_parser)

    subject = pc.diff(a_star_parser, aa_parser)

    actual = subject('a')
    assert actual.match == ['a']

    actual = subject('aaa')
    assert actual.match == ['a', 'a', 'a']

    with pytest.raises(pc.NoMatchException):
        subject('aa')


def test_followed_by():
    a_parser = pc.make_char('a')
    b_parser = pc.make_char('b')

    subject = pc.followed_by(a_parser, b_parser)

    actual = subject('abc')
    assert actual.match == 'a'

    with pytest.raises(pc.NoMatchException):
        subject('a')


def test_not_followed_by():
    a_parser = pc.make_char('a')
    b_parser = pc.make_char('b')

    subject = pc.not_followed_by(a_parser, b_parser)

    with pytest.raises(pc.NoMatchException):
        subject('abc')

    actual = subject('ac')
    assert actual.match == 'a'


def test_trace_parser():
    a_parser = pc.make_char('a')

    subject = pc.trace_parser(a_parser, 'test_name')
    actual = subject('a')
    assert actual.match == 'a'

    with pytest.raises(pc.NoMatchException):
        subject('b')


def test_search():
    one_star_parser = pc.plus(pc.make_const(lambda x: x == 1))
    subject = pc.pack(one_star_parser, sum)

    actual = subject.search([2, 1, 1, 1, 2, 1])
    assert actual == 3

    with pytest.raises(pc.NoMatchException):
        subject.search("1")


def test_search_all():
    one_star_parser = pc.plus(pc.make_const(lambda x: x == 1))
    subject = pc.pack(one_star_parser, sum)

    actuals = subject.search_all([2, 1, 1, 1, 2, 1])
    assert actuals[0] == 3
    assert actuals[1] == 1

    with pytest.raises(pc.NoMatchException):
        subject.search("1")
