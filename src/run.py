import os
import io
import subprocess
import pathlib
from main import create_parser


container_base_path = "/data"


def get_absolute_path(path: str) -> str:
    return os.path.abspath(path)


def map_path_to_container(path: str) -> str:
    return os.path.join(container_base_path, os.path.basename(path))


def main() -> None:
    parser = create_parser()
    args = parser.parse_args()

    image_name = "cut"
    docker_run_cmd = ["docker", "run", "-it"]

    # Process each argument and set up Docker volume mappings
    cargs = []
    for arg, value in vars(args).items():
        if arg == "command":
            continue
        if isinstance(value, io.IOBase):
            # Handle file objects opened by argparse.FileType
            file_path = value.name
            abs_path = get_absolute_path(file_path)
            cpath = container_base_path
            cargs.append(f"-{arg}")
            cargs.append(os.path.join(container_base_path, os.path.basename(abs_path)))
            docker_run_cmd.extend(["-v", f"{os.path.dirname(abs_path)}:{cpath}"])
        elif isinstance(value, pathlib.Path):
            # Handle pathlib.Path objects
            abs_path = get_absolute_path(str(value))
            cpath = map_path_to_container(abs_path)
            cargs.append(f"-{arg}")
            cargs.append(cpath)
            docker_run_cmd.extend(["-v", f"{abs_path}:{cpath}"])
        elif args.command == "serve" and arg == "p":
            cargs.append("-p")
            cargs.append(value)
            docker_run_cmd.extend(["-p", f"{value}:{value}"])
        else:
            cargs.append(f"-{arg}")
            cargs.append(value)

    # Add the image name and the arguments to the Docker command
    docker_run_cmd.append(image_name)
    docker_run_cmd.append("python")
    docker_run_cmd.append("main.py")
    docker_run_cmd.append(args.command)
    docker_run_cmd.extend(cargs)

    # print(docker_run_cmd)

    subprocess.run(docker_run_cmd)


if __name__ == "__main__":
    main()
