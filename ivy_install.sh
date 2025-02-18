#!/bin/sh -eu

ANTXML=${ANTXML:-./ant.xml}
IVYXML=${IVYXML:-./ivy.xml}
IVYSETTINGSXML=${IVYSETTINGSXML:-./settings.xml}
IVYCACHEDIR=${ICYCACHEDIR:-~/local/maven-repo/}
IVYLIBDIR=${IVYLIBDIR:-~/local/java/lib}
name="ivy"

while [ $# -gt 0 ]; do
    case "$1" in
        -d) IVYLIBDIR=$2 ; shift ;;
        -c) IVYCACHEDIR=$2 ; shift ;;
        -n) name=$2 ; shift ;;
        --) shift ; break ;;
        -*) echo "ERROR: Invalid option '$1' for $0" >&2 ; exit 64 ;;
        *) break ;;
    esac
    shift
done

# Build ivy.xml
cat > "$IVYXML" <<XML
<?xml version="1.0" encoding="UTF-8"?>
<ivy-module version="2.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://ant.apache.org/ivy/schemas/ivy.xsd">
<info organisation="apluslms" module="$name" revision="container" />
<dependencies defaultconf="default->master(default), compile(default), runtime(default)">
XML
while [ $# -gt 0 ]; do
    printf "  <dependency org=\"%s\" name=\"%s\" rev=\"%s\"" "$1" "$2" "$3" >> "$IVYXML"
    conf=${4:-}
    if [ "$conf" -a "${conf#*->}" != "$conf" ]; then
        printf " conf=\"%s\"" "$4" >> "$IVYXML"
        shift
    fi
    echo " />" >> "$IVYXML"
    shift 3
done
cat >> "$IVYXML" <<XML
</dependencies>
</ivy-module>
XML
cat "$IVYXML"

# NOTE: ivy standalone can't handle multiple types (doesn't parse comma)
#java \
#    "-Divy.lib.dir=$IVYLIBDIR" \
#    -jar /usr/share/java/ivy.jar \
#    -cache "$IVYCACHEDIR" \
#    -ivy "$IVYXML" -symlink -types jar,bundle \
#    -retrieve '${ivy.retrieve.pattern}'
#res=$?

tee "$IVYSETTINGSXML" <<XML
<?xml version="1.0" encoding="UTF-8"?>
<ivysettings>
    <include url="\${ivy.default.settings.dir}/ivysettings.xml" />
    <caches defaultCacheDir="$IVYCACHEDIR" />
</ivysettings>
XML

tee "$ANTXML" <<XML
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns:ivy="antlib:org.apache.ivy.ant" name="ivy" default="download jars">
    <property name="ivy.lib.dir" location="$IVYLIBDIR" />
    <target name="download jars">
        <ivy:configure file="$IVYSETTINGSXML" />
        <ivy:resolve file="$IVYXML" conf="default" />
        <ivy:retrieve type="jar,bundle" conf="default" symlink="true" />
    </target>
</project>
XML
        #<ivy:retrieve \${ivy.retrieve.pattern}" type="jar,bundle" conf="default" symlink="true" />

ant -lib /usr/share/java/ivy.jar -f "$ANTXML"
res=$?

rm -rf "$ANTXML" "$IVYSETTINGSXML" "$IVYXML"
find "$IVYCACHEDIR" \( -iname '*.properties' -o -iname 'ivy*.xml*' \) -exec rm {} \;
exit $res