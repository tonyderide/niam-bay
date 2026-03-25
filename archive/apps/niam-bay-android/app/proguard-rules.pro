# Ktor
-keep class io.ktor.** { *; }
-dontwarn io.ktor.**

# Kotlinx Serialization
-keepattributes *Annotation*, InnerClasses
-dontnote kotlinx.serialization.AnnotationsKt
-keepclassmembers class kotlinx.serialization.json.** { *** Companion; }
-keepclasseswithmembers class kotlinx.serialization.json.** { kotlinx.serialization.KSerializer serializer(...); }
-keep,includedescriptorclasses class com.niambay.app.**$$serializer { *; }
-keepclassmembers class com.niambay.app.** { *** Companion; }
-keepclasseswithmembers class com.niambay.app.** { kotlinx.serialization.KSerializer serializer(...); }
