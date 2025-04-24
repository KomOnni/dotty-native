import sys
import os

SCALA_PATH = "/Users/tammio1/Desktop/o1/devaus/scala3"
SCALA_FVER = "3.6.3"
SCALA_BRANCH = SCALA_FVER
SCALA_VER = "3"
MODULES_PATH = "/Users/tammio1/Desktop/o1/devaus/o1matsku/modules/solutions"
GRAALVM_PATH = "/Users/tammio1/Downloads/graalvm-jdk-21.0.7+8.1/Contents/Home"
GRADER_PATH = "/Users/tammio1/Desktop/o1/devaus/grade-o1"

CUR_DIR = os.getcwd()

# Check whether the script is run from the correct directory
if not os.path.exists('configsFromModules.sh'):
    print('Please run the script from the directory where it is located')
    sys.exit(1)

# Check that the variables are set
if SCALA_PATH == "" or SCALA_BRANCH == "" or MODULES_PATH == "" or GRAALVM_PATH == "":
    print('Please set the variables according to the README')
    sys.exit(1)

print('dotty-native.py')

os.environ['JAVA_HOME'] = GRAALVM_PATH
os.environ['PATH'] = os.environ['JAVA_HOME'] + '/bin:' + os.environ['PATH']

# Get the Scala compiler libraries
if int(SCALA_BRANCH.split('.')[1]) >= 6:
    COMPILER_JARS_PATH = os.path.join(SCALA_PATH, 'dist/target/republish/maven2')
    COMPILER_JARS = ':'.join([os.path.join(root, file) for root, _, files in os.walk(COMPILER_JARS_PATH) for file in files if file.endswith('.jar')])
    SCALA_COMPILER_LIBS = COMPILER_JARS
else:
    COMPILER_JARS_PATH = os.path.join(SCALA_PATH, 'dist/target/pack/lib/*')
    SCALA_COMPILER_LIBS = COMPILER_JARS_PATH + '*'

if not os.path.exists(os.path.join(os.environ['JAVA_HOME'], 'bin', 'native-image')):
    print('GraalVM is not set to JAVA_HOME, please set it according to the README')
    sys.exit(1)

# Check if native-image is installed
if os.system('native-image --version') != 0:
    print('GraalVM is not set to PATH, please install it according to the README')
    sys.exit(1)

# Check if Scala path exists and there is a copy of the Scala repository
if not os.path.exists(SCALA_PATH):
    print('Scala repository path does not exist, please set it according to the README')
    sys.exit(1)

# Run deps.py
if os.system('python3 deps.py --grader-path ' + GRADER_PATH + ' --scala-path ' + SCALA_PATH + ' --scala-fver ' + SCALA_FVER + ' --modules-path ' + MODULES_PATH) != 0:
    print('deps.py failed')
    sys.exit(1)

# Checkout the Scala branch and pull the latest changes
os.chdir(SCALA_PATH)
if os.system('git remote update origin --prune') != 0:
    print('git remote update origin --prune failed')
    sys.exit(1)
    
if os.system('git checkout ' + SCALA_BRANCH) != 0:
    print('git checkout ' + SCALA_BRANCH + ' failed')
    sys.exit(1)

## Do a reset to make sure that the repository is clean
if os.system('git reset --hard') != 0:
    print('git reset --hard failed')
    sys.exit(1)

## Remove scala3/dist/target if it exists
if os.path.exists('dist/target'):
    os.system('rm -r dist/target')

# Scala 3.6 changes the build command
if int(SCALA_BRANCH.split('.')[1]) >= 6:
    if os.system('sbt "dist / Universal /  packageBin"') != 0:
        print('sbt dist / Universal /  packageBin failed')
        sys.exit(1)
else:
    if os.system('sbt "dist / pack"') != 0:
        print('sbt dist / pack failed')
        sys.exit(1)

        # Run sbt "export scala3-library / fullClasspath" and get the last line of the output
os.chdir(SCALA_PATH)
if os.system('sbt "export scala3-library / fullClasspath" > classpath.txt') != 0:
    print('sbt export scala3-library / fullClasspath failed')
    sys.exit(1)

with open('classpath.txt', 'r') as f:
    lines = f.readlines()
    classpath = lines[-1].strip()

# Set SCALA_LIB
print('SCALA_LIB = ' + classpath)
SCALA_LIB = classpath
os.environ['SCALA_LIB'] = SCALA_LIB

print('Please make sure that the libraries are current ones in lib/')
os.chdir(CUR_DIR)

# Remove tmp-script if it exists
if os.path.exists('tmp-script'):
    os.system('rm -r tmp-script')

# Remove native-image-config if it exists
if os.path.exists('native-image-config'):
    os.system('rm -r native-image-config')

if os.system('./configsFromModules.sh tmp-script ' + MODULES_PATH + ' ' + SCALA_PATH + ' ' + COMPILER_JARS_PATH) != 0:
    print('configsFromModules.sh failed')
    sys.exit(1)

# Scala version of Java runtime
os.system('scala rt.scala')

# Create pgo dotty-native
os.system(f'native-image -o dotty-native-instrumented -cp \'{SCALA_COMPILER_LIBS}:./lib/*\' --pgo-instrument --no-fallback -H:ConfigurationFileDirectories=native-image-config dotty.tools.dotc.Main')

# Run pgo
os.system('mkdir instrumented')
os.system('echo \'@main def main = println("Hello world")\' > hello.scala')
os.system(f'./dotty-native-instrumented -bootclasspath ./extracted-rt.jar -d instrumented -cp {SCALA_LIB} hello.scala')

# Create native image
os.system(f'native-image -o dotty-native -cp \'{SCALA_COMPILER_LIBS}:./lib/*\' --pgo --no-fallback -H:ConfigurationFileDirectories=native-image-config dotty.tools.dotc.Main')

print('dotty-native created, checking if it works')
os.system('mkdir compiled-native')
os.system(f'./dotty-native -bootclasspath ./extracted-rt.jar -d compiled-native -cp {SCALA_LIB} hello.scala')
if os.system('java -cp $SCALA_LIB:./compiled-native main') != 0:
    print('dotty-native does not work')
    sys.exit(1)

print('dotty-native works')

# Remove temporary files
os.system('rm -r lib')
os.system('rm -r tmp-script')
os.system('rm -r instrumented')
os.system('rm -r compiled-native')
os.remove('hello.scala')
os.remove('dotty-native-instrumented')
os.remove('default.iprof')

# Remove useless files
os.system('rm *.so')