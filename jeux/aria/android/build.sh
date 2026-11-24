#!/bin/bash
# Fabrique aria.apk sans Gradle : aapt2 + javac + d8 + apksigner (SDK Android 34).
set -e; cd "$(dirname "$0")"
SDK=${ANDROID_HOME:-$HOME/Android/Sdk}; BT=$SDK/build-tools/34.0.0; JAR=$SDK/platforms/android-34/android.jar
rm -rf out; mkdir -p out/classes out/dex; cp ../index.html assets/index.html
$BT/aapt2 compile --dir res -o out/res.zip
$BT/aapt2 link -o out/base.apk -I $JAR --manifest AndroidManifest.xml -A assets out/res.zip
javac -nowarn --release 11 -cp $JAR -d out/classes src/fr/niambay/aria/*.java 2>&1 | grep -v "^warning\|^Note" || true
$BT/d8 --lib $JAR --output out/dex $(find out/classes -name '*.class')
(cd out/dex && zip -q -j ../base.apk classes.dex)
$BT/zipalign -f 4 out/base.apk out/aligned.apk
KS=$HOME/.android/debug.keystore
[ -f $KS ] || { mkdir -p $HOME/.android; keytool -genkeypair -keystore $KS -storepass android -keypass android -alias androiddebugkey -keyalg RSA -keysize 2048 -validity 10000 -dname "CN=Android Debug,O=Android,C=US" >/dev/null 2>&1; }
$BT/apksigner sign --ks $KS --ks-pass pass:android --key-pass pass:android --out aria.apk out/aligned.apk
$BT/apksigner verify aria.apk && ls -la aria.apk
