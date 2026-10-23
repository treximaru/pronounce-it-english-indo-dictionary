package com.kamus.kamus_pronunciation

import android.content.Context
import android.os.Handler
import android.os.Looper
import android.view.inputmethod.InputMethodManager
import io.flutter.embedding.android.FlutterActivity

class MainActivity : FlutterActivity() {
    // This is a search-first dictionary: whenever the window comes to the
    // foreground, force the soft keyboard up. The Dart side keeps the
    // search field focused; this native fallback exists because some OEM
    // ROMs (e.g. MIUI) ignore implicit keyboard-show requests at launch.
    override fun onWindowFocusChanged(hasFocus: Boolean) {
        super.onWindowFocusChanged(hasFocus)
        if (hasFocus) {
            Handler(Looper.getMainLooper()).postDelayed({
                val imm = getSystemService(Context.INPUT_METHOD_SERVICE) as InputMethodManager
                imm.showSoftInput(window.decorView, InputMethodManager.SHOW_FORCED)
            }, 400)
        }
    }
}
