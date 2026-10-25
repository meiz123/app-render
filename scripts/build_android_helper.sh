#!/bin/zsh
set -eu
cd -- "${0:A:h:h}"
sdk_dir="${ANDROID_SDK_ROOT:-$HOME/Library/Android/sdk}"
jdk_dir="${JAVA_HOME:-/Applications/Android Studio.app/Contents/jbr/Contents/Home}"
platform_jar="${FRAMELAB_ANDROID_JAR:-$sdk_dir/platforms/android-37.0/android.jar}"
mkdir -p build/android-helper/classes build/android-helper/dex framelab/assets
"$jdk_dir/bin/javac" --release 8 -cp "$platform_jar" -d build/android-helper/classes android-helper/src/com/framelab/AppCatalog.java
"$jdk_dir/bin/java" -cp "$sdk_dir/build-tools/36.0.0/lib/d8.jar" com.android.tools.r8.D8 --min-api 23 --lib "$platform_jar" --output build/android-helper/dex build/android-helper/classes/com/framelab/AppCatalog.class
cp build/android-helper/dex/classes.dex framelab/assets/app-catalog.dex
