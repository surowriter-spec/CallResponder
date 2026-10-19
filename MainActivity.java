package com.surowriter.callresponder;

import android.Manifest;
import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.provider.Settings;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

public class MainActivity extends Activity {
    static final String PREFS = "cr";
    static final String KEY_MSG = "msg";
    static final String DEFAULT_MSG =
        "This is an automated reply. Please do not call repeatedly. "
        + "Send your payment query by email or S M S only. "
        + "Calls are being logged, and repeated calls will be reported to the R B I Ombudsman. Thank you.";

    EditText msg;
    TextView logView;

    @Override
    protected void onCreate(Bundle b) {
        super.onCreate(b);
        SharedPreferences sp = getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        int pad = (int) (16 * getResources().getDisplayMetrics().density);

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(pad, pad * 2, pad, pad);

        TextView title = new TextView(this);
        title.setText("CallResponder");
        title.setTextSize(24);
        root.addView(title);

        TextView hint = new TextView(this);
        hint.setText("Message to play to unknown callers:");
        root.addView(hint);

        msg = new EditText(this);
        msg.setMinLines(4);
        msg.setText(sp.getString(KEY_MSG, DEFAULT_MSG));
        root.addView(msg);

        Button start = new Button(this);
        start.setText("Save and START");
        start.setOnClickListener(v -> startFlow());
        root.addView(start);

        Button stop = new Button(this);
        stop.setText("STOP");
        stop.setOnClickListener(v -> stopService(new Intent(this, ResponderService.class)));
        root.addView(stop);

        Button batt = new Button(this);
        batt.setText("Allow running in background (battery)");
        batt.setOnClickListener(v -> {
            try {
                startActivity(new Intent(Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS,
                        Uri.parse("package:" + getPackageName())));
            } catch (Exception ignored) { }
        });
        root.addView(batt);

        Button refresh = new Button(this);
        refresh.setText("Refresh call log");
        refresh.setOnClickListener(v -> showLog());
        root.addView(refresh);

        logView = new TextView(this);
        ScrollView sv = new ScrollView(this);
        sv.addView(logView);
        root.addView(sv);
        setContentView(root);
        showLog();
    }

    @Override
    protected void onResume() {
        super.onResume();
        showLog();
    }

    void showLog() {
        logView.setText(ResponderService.readLog(this));
    }

    String[] perms() {
        if (Build.VERSION.SDK_INT >= 33) {
            return new String[]{Manifest.permission.READ_PHONE_STATE, Manifest.permission.READ_CALL_LOG,
                    Manifest.permission.READ_CONTACTS, Manifest.permission.ANSWER_PHONE_CALLS,
                    Manifest.permission.POST_NOTIFICATIONS};
        }
        return new String[]{Manifest.permission.READ_PHONE_STATE, Manifest.permission.READ_CALL_LOG,
                Manifest.permission.READ_CONTACTS, Manifest.permission.ANSWER_PHONE_CALLS};
    }

    boolean hasAll() {
        for (String p : perms()) {
            if (checkSelfPermission(p) != PackageManager.PERMISSION_GRANTED) return false;
        }
        return true;
    }

    void startFlow() {
        getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit()
                .putString(KEY_MSG, msg.getText().toString()).apply();
        if (hasAll()) {
            startForegroundService(new Intent(this, ResponderService.class));
        } else {
            requestPermissions(perms(), 1);
        }
    }

    @Override
    public void onRequestPermissionsResult(int code, String[] p, int[] r) {
        super.onRequestPermissionsResult(code, p, r);
        if (hasAll()) {
            startForegroundService(new Intent(this, ResponderService.class));
        }
    }
}
