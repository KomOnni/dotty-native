## Table of contents

1. Introduction
2. How to build a native-image of dotty
3. How to use the native-image of dotty
4. Credentials

### Introduction

Dotty-native is a native-image of Scala 3 (dotty) compiler, which can eliminate Scala's compiler startup time. It is used in exercise graders for Scala programming courses at Aalto University to speed up compilation. The average speedup from this approach has been more than 10 seconds (~14s -> ~2s) in compilation phase, which was and still is the slowest part in the graders. It is used as a possible speedup and in case it fails, the normal Scala compiler is run to compile or give compiler errors to students.

The dotty-native file in the repository is made with linux x86 and has worked with Ubuntu 22.04 and 24.04.

This approach is limited to certain few usecases as one needs to know reflections and macros used in compilation before making the native-image compiler. Many libraries use reflections/macros in compilation phase and these need to be known before making the native executable of the compiler. The native compiler usually fails when, for example, an unknown library is imported, even if it is not used. Also the errors in these cases, where unknown libraries are imported, are neither novice-friendly nor user-friendly. Another bug in the compiler is that it does not return an error code, so one can, for example, check whether it has created any files to know has it worked.

This repository includes a ```configsFromModules.sh``` script, which can make configuration files from multiple different modules inside a certain folder, so compilation with the native-image compiler works for all of them. For O1 this fails at some modules due to sed commands used in grading but this still works.

This approach was tested on 200000 student submissions. All but around 200 submissions behaved as expected, and of the 200 submissions, each had a "weird" import.

### How to build a native image of dotty

1. Download GraalVM (https://www.graalvm.org/downloads/) and set the JAVA_HOME and PATH environment variables. Also check that these are correct (versions do not matter). I suggest saving these commands.

    ```
    export JAVA_HOME=/PATH/TO/GRAALVM/
    export PATH=/PATH/TO/GRAALVM/bin:$PATH
    ```
    e.g.
    ```
    export JAVA_HOME=/home/komonni/Downloads/graalvm-jdk-17.0.10+11.1
    export PATH=/home/komonni/Downloads/graalvm-jdk-17.0.10+11.1/bin:$PATH
    ```

    ```
    java -version

    Java(TM) SE Runtime Environment Oracle GraalVM 21.0.2+13.1 (build 21.0.2+13-LTS-jvmci-23.1-b30)
    Java HotSpot(TM) 64-Bit Server VM Oracle GraalVM 21.0.2+13.1 (build 21.0.2+13-LTS-jvmci-23.1-b30, mixed mode, sharing)
    ```

    ```
    native-image --version

    GraalVM Runtime Environment Oracle GraalVM 21.0.2+13.1 (build 21.0.2+13-LTS-jvmci-23.1-b30)
    Substrate VM Oracle GraalVM 21.0.2+13.1 (build 21.0.2+13-LTS, serial gc, compressed references)
    ```

2. Clone scala3 (dotty) into a new folder, switch to the correct branch (corresponding to the Scala version), and build it.

    ```
    cd ..
    git clone git@github.com:scala/scala3.git
    cd scala3
    git checkout release-<SCALA VERSION>
    sbt "dist / pack"
    ```

3. Copy the dotty.scala file from this folder to the scala3 folder to simplify the creation of the native image. *Make sure that dotty.scala has the correct scala-compiler version defined in the file*

    ```
    cp ../dotty-native/dotty.scala .
    ```

4. Set the SCALA_LIB variable.

    ```
    sbt "export scala3-library / fullClasspath"
    ➜...
    ➜/home/komonni/Projects/O1HeadTA/Misc/scala3/library/target/scala-3.4.0/classes:/home/komonni/.cache/coursier/v1/https/repo1.maven.org/maven2/org/scala-lang/scala-library/2.13.12/scala-library-2.13.12.jar

    export SCALA_LIB="</PATH/TO/SCALA3LIBRARY>"
    ```

5. Put your libraries' JAR files in a `lib` folder at the root of the project.

    The lib folder already contains the libraries O1 uses as of 24.4.2024.
    The libraries for O1 were copied from a paused grader container.

6. Make configuration files for native-image.
    
    This is needed because dotty-native needs to know the used reflections and macros. This can be done automatically with a GraalVM java flag. This repo includes a script to make configuration files from multiple modules inside a folder which can be used, or then one can do manually.

    1. For multiple modukes:
    
        Run the ```configsFromModules.sh``` script for the native image configuration files. Remember to change the SCALA_PATH and MODULES_PATH variables. The script can take a lot of time as it starts a new scalac instance for each module in the MODULES_PATH directory.

        The script takes a folder name as argument. Without the argument, it defaults to `tmp-config`. The script removes nati

        ```
        cd ../dotty-native
        ./configsFromModules.sh <tmp-folder-name>
        ```

    2. For a single module or demo:
    
        native-image-configuration files by running dotty on a file to compile. If you need dotty-native to compile scala files with libraries, remember to use them here aswell. Here is an example to compile hello.scala

        ```
        cd ../dotty-native
        mkdir compiled
        echo '@main def main = println("Hello world")' > hello.scala
        java -cp '../scala3/dist/target/pack/lib/*' -agentlib:native-image-agent=config-output-dir=native-image-config dotty.tools.dotc.Main -d compiled -cp $SCALA_LIB hello.scala
        ```

        Check that you can run the normally compiled file

        ```
        java -cp $SCALA_LIB:./compiled main
        ```

7. Create native executable of dotty

    ```
    scala-cli --power package ./../scala3/dotty.scala -o dotty-native -cp ./lib/* --main-class main --native-image -f --jvm 17 -- --no-fallback -H:ConfigurationFileDirectories=native-image-config
    ```

8. Extract the Java runtime JAR for dotty-native as Scala

    This is because the native image does not support the default boot classpath JARs. This runtime jar includes only ```java.base``` and ```java.desktop``` modules by default, but more can be added.

    ```
    scala rt.scala
    ```

9. Check that one can compile with dotty-native and run the compiled file. 

    Here again is an example of hello.scala

    ```
    mkdir compiled-native
    echo '@main def main = println("Hello world")' > hello.scala
    ./dotty-native -bootclasspath ./extracted-rt.jar -d compiled-native -cp $SCALA_LIB hello.scala
    java -cp $SCALA_LIB:./compiled-native main
    ```

### How to use the native-image of dotty

Here is how you can use the native image compiler.

```
./dotty-native -bootclasspath ./extracted-rt.jar -d <WHERE_TO_COMPILE> -cp $SCALA_LIB:<LIB_FOLDER> <FILES_TO_COMPILE>

java -cp $SCALA_LIB <COMPILED_FOLDER> <class to run>
```

### Credentials

Onni Komulainen, @komonni in GitHub

A lot has been taken from @mbovel here:
    https://github.com/oracle/graal/issues/8371