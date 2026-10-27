plugins { id("com.android.application"); id("org.jetbrains.kotlin.android") }

android {
    namespace = "com.shoowt.snapload"
    compileSdk = 35
    defaultConfig {
        applicationId = "com.shoowt.snapload"
        minSdk = 29
        targetSdk = 35
        versionCode = 3
        versionName = "1.0.2"
        ndk { abiFilters += listOf("arm64-v8a", "armeabi-v7a", "x86_64") }
    }
    signingConfigs {
        create("release") {
            storeFile = file(System.getenv("SNAPLOAD_KEYSTORE") ?: "../../signing/snapload.jks")
            storePassword = System.getenv("SNAPLOAD_STORE_PASSWORD")
            keyAlias = "snapload"
            keyPassword = System.getenv("SNAPLOAD_KEY_PASSWORD")
        }
    }
    buildTypes { getByName("release") { signingConfig = signingConfigs.getByName("release") } }
    packaging { jniLibs { useLegacyPackaging = true } }
    compileOptions { sourceCompatibility = JavaVersion.VERSION_17; targetCompatibility = JavaVersion.VERSION_17 }
    kotlinOptions { jvmTarget = "17" }
}
dependencies {
    implementation("io.github.junkfood02.youtubedl-android:library:0.18.1")
    implementation("io.github.junkfood02.youtubedl-android:ffmpeg:0.18.1")
}
