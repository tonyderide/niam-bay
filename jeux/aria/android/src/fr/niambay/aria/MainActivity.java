package fr.niambay.aria;
import android.app.Activity;
import android.os.Bundle;
import android.view.View;
import android.webkit.WebSettings;
import android.webkit.WebView;
public class MainActivity extends Activity {
    private WebView w;
    @Override protected void onCreate(Bundle b) {
        super.onCreate(b);
        w = new WebView(this);
        WebSettings s = w.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setMediaPlaybackRequiresUserGesture(false);
        w.setBackgroundColor(0xFF07080A);
        w.setOverScrollMode(View.OVER_SCROLL_NEVER);
        setContentView(w);
        if (b == null) w.loadUrl("file:///android_asset/index.html"); else w.restoreState(b);
    }
    @Override protected void onSaveInstanceState(Bundle b) { super.onSaveInstanceState(b); w.saveState(b); }
    @Override public void onWindowFocusChanged(boolean f) {
        super.onWindowFocusChanged(f);
        if (f) getWindow().getDecorView().setSystemUiVisibility(View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY | View.SYSTEM_UI_FLAG_FULLSCREEN | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION | View.SYSTEM_UI_FLAG_LAYOUT_STABLE);
    }
}
