import logging

from args import Parser, get_subcommands

logging.basicConfig(level=logging.INFO, format='{"level"="%(levelname)s", "time"="%(asctime)s", "msg"="%(message)s"}')


def main():
    args, unknown_args = Parser(get_subcommands()).parse()
    args.func(args, unknown_args)
