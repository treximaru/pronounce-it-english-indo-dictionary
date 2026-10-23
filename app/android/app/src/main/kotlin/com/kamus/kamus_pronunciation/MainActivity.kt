package com.kamus.kamus_pronunciation

import android.content.Context
import android.os.Handler
import android.os.Looper
import android.view.WindowInsets
import android.view.inputmethod.InputMethodManager
import io.flutter.embedding.android.FlutterActivity

class MainActivity : FlutterActivity() {
    // Search-first dictionary: the keyboard must be up whenever the app is
    // in the foreground. The Dart side keeps the search field focused (the
    // cursor blinks), but on some OEM ROMs (MIUI) a single keyboard-show
    // request is silently dropped if it lands before Flutter's text-input
    // connection exists, or if it targets the wrong view. So: retry against
    // the actually-focused view until the IME is really visible.
    private val keyboardHandler = Handler(Looper.getMainLooper())
    private var keyboardAttempts = 0

    private val keyboardRunnable = object : Runnable {
        override fun run() {
            val imm = getSystemService(Context.INPUT_METHOD_SERVICE) as InputMethodManager
            val target = window.decorView.findFocus() ?: window.decorView
            val imeVisible =
                window.decorView.rootWindowInsets?.isVisible(WindowInsets.Type.ime()) == true
            if (!imeVisible) {
                imm.showSoftInput(target, 0)
                keyboardAttempts++
                if (keyboardAttempts < 10) {
                    keyboardHandler.postDelayed(this, 300)
                }
            }
        }
    }

    override fun onWindowFocusChanged(hasFocus: Boolean) {
        super.onWindowFocusChanged(hasFocus)
        keyboardHandler.removeCallbacks(keyboardRunnable)
        if (hasFocus) {
            keyboardAttempts = 0
            keyboardHandler.postDelayed(keyboardRunnable, 300)
        }
    }
}
