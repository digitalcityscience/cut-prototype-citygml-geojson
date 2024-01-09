import argparse
import pathlib


def create_parser():
    parser = argparse.ArgumentParser(add_help=False)

    command_parser = argparse.ArgumentParser()
    subparsers = command_parser.add_subparsers(title="Commands", dest="command")
    subparsers.required = True

    convert_parser = subparsers.add_parser("convert", parents=[parser], help="convert gml to geojson")
    convert_parser.add_argument(
        "-d",
        required=False,
        help="source directory where gml files are located",
        default=pathlib.Path('./data/LoD2_CityGML_HH_2016'),
        type=pathlib.Path
    )
    convert_parser.add_argument(
        "-o",
        required=False,
        help="target directory to put geojson",
        default=pathlib.Path('./data/out'),
        type=pathlib.Path
    )
    createdb_parser = subparsers.add_parser(
        "createdb", parents=[parser], help="create sqlite database from geojson files")
    createdb_parser.add_argument(
        "-p",
        required=False,
        help="directory with geojson files",
        default=pathlib.Path('./data/out'),
        type=pathlib.Path
    )
    createdb_parser.add_argument(
        "-d",
        required=False,
        help="database output path",
        default='./data/out/footprints.db',
        type=argparse.FileType('w', encoding='latin-1')
    )
    serve_parser = subparsers.add_parser("serve", parents=[parser], help="start server")
    serve_parser .add_argument(
        "-d",
        required=False,
        help="database path",
        default='./data/out/footprints.db',
        type=argparse.FileType('r', encoding='latin-1')
    )
    serve_parser.add_argument(
        "-p",
        help="Port for api server",
        default="5000"
    )
    return command_parser


if __name__ == '__main__':

    args = create_parser().parse_args()

    if args.command == 'convert':
        from convert import convert
        convert(args.d.absolute(), args.o.absolute())
    elif args.command == 'createdb':
        from create_db import create_db
        create_db(args.p.absolute(), args.d.name)
    elif args.command == 'serve':
        from server import Server
        Server(args.p, args.d.name).run()
