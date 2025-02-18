#!/usr/bin/env bash

#Change these
MODULES_PATH=${2:-"/home/komonni/Projects/O1HeadTA/o1matsku/modules/solutions"}
SCALA_PATH=${3:-"/home/komonni/Projects/O1HeadTA/scala3"}

SCALACFLAGS="-encoding utf-8 -language:postfixOps -Xno-colors"
DIRECTORY=${1:-tmp-config}

if [[ -z "$SCALA_LIB" ]]; then
  echo "Variable SCALA_LIB is not set"
  exit 1
fi

if [[ -z "${JAVA_HOME}" ]]; then
  echo "JAVA_HOME is not set"
  exit 1
fi

if [[ $PATH != *"${JAVA_HOME}/bin"* ]]; then
  echo "JAVA_HOME/bin is not in the PATH"
  exit 1
fi

if [ -d "$DIRECTORY" ]; then
  echo "The directory '$DIRECTORY' exists."
  exit 1
fi

# Uncomment the line below this incase you want to automatically remove the native-image-config in the root of the project
#rm -r ../native-image-config

if [ -d "native-image-config" ]; then
  echo "The directory native-image-config exists, rename or remove it beforehand."
  exit 1
fi

echo "The directory, where config files are created, is: $DIRECTORY"

AMOUNT_OF_MODULES=$(find $MODULES_PATH -mindepth 1 -maxdepth 1 -type d | wc -l)

mkdir "$DIRECTORY"
cd "$DIRECTORY" || exit 1
mkdir configs
mkdir compiled
mkdir logs

i=1
for dir in "$MODULES_PATH"/* ; do
  if [[ -d "$dir" ]]; then
    name="$(basename "$dir")"
    files=$(find "$dir" -type f -name "*.scala" | tr '\n' ' ')
    echo "$i/$AMOUNT_OF_MODULES, $name"
    mkdir configs/"$name"
    mkdir compiled/"$name"
    java -cp "$SCALA_PATH/dist/target/pack/lib/*" -agentlib:native-image-agent=config-output-dir=configs/"$name" dotty.tools.dotc.Main "$SCALACFLAGS" -d compiled/"$name" -cp "$SCALA_LIB":../lib/*:"$dir"/lib/* $files 2> ./logs/"$name".txt  1> ./logs/"$name".txt
    RES=$?
    [ $RES -eq 1 ] && echo "Compilation failed, log file is in $DIRECTORY/logs/$name.txt"
    i=$((i+1))
  fi
done

mkdir native-image-config
mkdir native-image-config/agent-extracted-predefined-classes

array_files=("jni-config.json" "predefined-classes-config.json" "proxy-config.json" "reflect-config.json")
object_files=("resource-config.json" "serialization-config.json")

for file in "${array_files[@]}"; do
  combined_json='[]'

  for dir in ./configs/*/; do
    if [ -s "${dir}${file}" ]; then
      combined_json=$(jq -s '.[0] + .[1] | unique' <(echo "$combined_json") "${dir}${file}")
    fi
  done
  echo "$combined_json" | jq '.' > "native-image-config/${file}"
done

for file in "${object_files[@]}"; do
  combined_json='{}'

  for dir in ./configs/*/; do
    if [ -s "${dir}${file}" ]; then
      combined_json=$(jq -s '.[0] * .[1]' <(echo "$combined_json") "${dir}${file}")
    fi
  done
  echo "$combined_json" | jq '.' > "native-image-config/${file}"
done

cp -r native-image-config ../