import os
import sys
import argparse

# Check the default values of the arguments
parser = argparse.ArgumentParser(description='Process some paths and versions.')
parser.add_argument('--grader-path', default='../grade-o1', help='Path to the grader directory')
parser.add_argument('--scala-path', default='../scala', help='Path to the Scala directory')
parser.add_argument('--scala-fver', default='3.3.4', help='Scala version')
parser.add_argument('--modules-path', default='../o1matsku/modules/solutions', help='Path to the modules directory')

args = parser.parse_args()

GRADER_PATH = args.grader_path
SCALA_PATH = args.scala_path
SCALA_FVER = args.scala_fver
SCALA_VER = args.scala_fver.split('.')[0]
MODULES_PATH = args.modules_path


# Parse Dockerfile for all libraries (lines starting with org)
def parse_dockerfile(dockerfile):
    libraries = []
    with open(dockerfile, 'r') as f:
        lines = f.readlines()
        for line in lines:
            line = line.strip()
            if line.startswith('org'):
                line = line.replace('$SCALA_FVER', SCALA_FVER)
                line = line.replace('$SCALA_VER', SCALA_VER)
                line = line.replace('$SCALA_PATH', SCALA_PATH)
                line = line.replace('\\', '')
                libraries.append(line)
    return libraries

libraries = parse_dockerfile(GRADER_PATH + '/Dockerfile')

# Install all libraries to ./lib
for library in libraries:
    if os.system(f'./ivy_install.sh -n autolibs -d "lib" ' + library) != 0:
        print('ivy_install.sh failed')
        sys.exit(1)

# Add libmanual to lib
os.system(f'cp -r ./libmanual/* lib')

# Add modules libraries to lib
os.system(f'cp -r {MODULES_PATH}/*/lib/* lib')