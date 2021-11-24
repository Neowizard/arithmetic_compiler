class NoMatchException(Exception):
    def __init__(self, tokens, index):
        msg = f'No match at index {index} for token list: {tokens}'
        super().__init__(self, msg)


class ParserOutput:
    def __init__(self, match, next_token_index):
        self.match = match
        self.next_token_index = next_token_index

    @staticmethod
    def empty_output(index):
        # Defining an empty output to be an output whose match equals the output itself
        # This prevents a conflict between an empty match and match against "None"
        output = ParserOutput(None, index)
        output.match = output
        return output

    def is_empty_output(self):
        return self.match == self

    def __repr__(self):
        return f'ParserOutput({self.match}, {self.next_token_index})'


class Parser:
    def __init__(self, parse_func):
        self._parse = parse_func

    def parse(self, tokens, index):
        return self._parse(tokens, index)

    def __call__(self, tokens, index=0):
        return self.parse(tokens, index)

    def _search(self, tokens, index):
        for i in range(index, len(tokens)):
            try:
                parser_output = self(tokens, i)
                return parser_output
            except NoMatchException:
                continue

        raise NoMatchException(tokens, -1)

    def search(self, tokens):
        return self._search(tokens, 0).match

    def search_all(self, tokens):
        i = 0
        outputs = []
        while i < len(tokens):
            parser_output = self._search(tokens, i)
            i = parser_output.next_token_index
            outputs.append(parser_output.match)

        return outputs


def make_const(pred):
    def parse(tokens, index):
        if index >= len(tokens):
            raise NoMatchException(tokens, index)
        token = tokens[index]
        if pred(token):
            return ParserOutput(token, index + 1)
        else:
            raise NoMatchException(tokens, index)

    return Parser(parse)


def make_char(c):
    def pred(token):
        return token == c

    return make_const(pred)


def make_char_ci(c):
    def pred(token):
        return token.lower() == c.lower()

    return make_const(pred)


def make_word(word):
    parsers = []
    for c in word:
        parsers.append(make_char(c))
    return caten_list(parsers)


def make_oneof(chars):
    return disj_list([make_char(c) for c in chars])


def make_char_range(start, end):
    start = ord(start)
    end = ord(end)

    def pred(token):
        token = ord(token)
        return start <= token <= end

    return make_const(pred)


def make_char_range_ci(start, end):
    start = ord(start.lower())
    end = ord(end.lower())

    def pred(token):
        token = ord(token.lower())
        return start <= token <= end

    return make_const(pred)


def _make_empty():
    def parse(tokens, index):
        raise NoMatchException(tokens, index)

    return Parser(parse)


def _make_end_of_input():
    def parse(tokens, index):
        if len(tokens) != index:
            raise NoMatchException(tokens, index)
        else:
            return ParserOutput.empty_output(index)

    return Parser(parse)


EPSILON = ()

epsilon_parser = Parser(lambda tokens, index: ParserOutput(EPSILON, index))
empty_parser = _make_empty()
end_of_input_parser = _make_end_of_input()
any_parser = make_const(lambda *_: True)


def caten(parser1, parser2):
    def parse(tokens, index):
        parser1_output = parser1(tokens, index)
        parser1_match = parser1_output.match

        parser2_start_index = parser1_output.next_token_index
        parser2_output = parser2(tokens, parser2_start_index)
        parser2_match = parser2_output.match

        match = (parser1_match, parser2_match)
        next_token_index = parser2_output.next_token_index
        return ParserOutput(match, next_token_index)

    return Parser(parse)


def caten_list(parsers):
    catenation = epsilon_parser
    for parser in parsers:
        catenation = caten(catenation, parser)

    def flatten_catenation(matches):
        if len(matches) == 0:
            return ()
        else:
            head = flatten_catenation(matches[0])
        tail = matches[1:]
        return head + tail

    catenation = pack(catenation, flatten_catenation)
    return catenation


def pack(parser, transformation):
    def parse(tokens, index):
        parser_output = parser(tokens, index)

        match = transformation(parser_output.match)
        next_token_index = parser_output.next_token_index
        return ParserOutput(match, next_token_index)

    return Parser(parse)


def disj(parser1, parser2):
    def parse(tokens, index):
        try:
            parser_output = parser1(tokens, index)
        except NoMatchException:
            parser_output = parser2(tokens, index)

        return parser_output

    return Parser(parse)


def disj_list(parsers):
    disjunction = empty_parser
    for parser in parsers:
        disjunction = disj(parser, disjunction)

    return disjunction


def star(parser):
    def parse(tokens, index):
        matches = []
        try:
            while True:
                parser_output = parser(tokens, index)
                matches.append(parser_output.match)
                index = parser_output.next_token_index
        except NoMatchException:
            parser_output = ParserOutput(matches, index)

        return parser_output

    return Parser(parse)


def plus(parser):
    head = parser
    tail = star(parser)

    def flatten(matches):
        head = matches[0]
        tail = matches[1]
        return [head] + tail

    return pack(caten(head, tail), flatten)


def delayed(make_parser):
    def parse(tokens, index):
        parser = make_parser()
        return parser(tokens, index)

    return Parser(parse)


def guard(parser, predicate):
    def parse(tokens, index):
        parser_output = parser(tokens, index)
        if predicate(parser_output.match):
            return parser_output
        else:
            raise NoMatchException(tokens, index)

    return Parser(parse)


def diff(parser1, parser2):
    def parse(tokens, index):
        parser1_output = parser1(tokens, index)
        try:
            parser2(tokens, index)
        except NoMatchException:
            return parser1_output

        raise NoMatchException(tokens, index)

    return Parser(parse)


def followed_by(parser1, parser2):
    def parse(tokens, index):
        parser1_output = parser1(tokens, index)

        parser2_index = parser1_output.next_token_index
        parser2(tokens, parser2_index)

        return parser1_output

    return Parser(parse)


def not_followed_by(parser1, parser2):
    def parse(tokens, index):
        parser1_output = parser1(tokens, index)

        parser2_index = parser1_output.next_token_index
        try:
            parser2(tokens, parser2_index)
        except NoMatchException:
            return parser1_output

        raise NoMatchException(tokens, index)

    return Parser(parse)


def trace_parser(parser, name):
    def parse(tokens, index):
        try:
            parser_output = parser(tokens, index)
            print(f'{name}: match from {index}:\n'
                  f'------\n'
                  f'{parser_output}'
                  f'======')
            return parser_output
        except NoMatchException:
            print(f'{name}: Failed to match from {index} against tokens: {tokens}')
            raise

    return Parser(parse)
