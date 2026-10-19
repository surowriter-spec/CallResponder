package com.surowriter.callresponder;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.Service;
import android.content.Context;
import android.content.Intent;
import android.content.pm.ServiceInfo;
import android.database.Cursor;
import android.media.AudioAttributes;
import android.media.AudioDeviceInfo;
import android.media.AudioManager;
import android.telephony.SmsManager;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.IBinder;
import android.os.Looper;
import android.provider.ContactsContract;
import android.speech.tts.TextToSpeech;
import android.speech.tts.UtteranceProgressListener;
import android.telecom.TelecomManager;
import android.telephony.PhoneStateListener;
import android.telephony.TelephonyManager;

import java.io.File;
import java.io.FileWriter;
import java.io.FileReader;
import java.io.BufferedReader;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Date;
import java.util.Locale;

public class ResponderService extends Service {
    static final long ANSWER_DELAY_MS = 3500;
    static final long MAX_CALL_MS = 60000;

    TelephonyManager tm;
    TelecomManager telecom;
    AudioManager am;
    TextToSpeech tts;
    boolean ttsReady = false;
    PhoneStateListener listener;
    final Handler h = new Handler(Looper.getMainLooper());

    String lastNumber = "";
    boolean scheduled = false;
    boolean weAnswered = false;
    int savedMusicVol = -1;

    final Runnable answerTask = new Runnable() {
        @Override public void run() {
            scheduled = false;
            if (isContact(lastNumber)) {
                log("SKIPPED (saved contact) " + lastNumber);
                return;
            }
            sendSmsOnce(lastNumber);
            try {
                telecom.acceptRingingCall();
                weAnswered = true;
                log("ANSWERED " + (lastNumber.isEmpty() ? "(hidden number)" : lastNumber));
            } catch (Exception e) {
                log("ERROR answering: " + e.getMessage());
            }
        }
    };

    final Runnable hangup = new Runnable() {
        @Override public void run() { endCallNow(); }
    };

    @Override
    public void onCreate() {
        super.onCreate();
        tm = (TelephonyManager) getSystemService(Context.TELEPHONY_SERVICE);
        telecom = (TelecomManager) getSystemService(Context.TELECOM_SERVICE);
        am = (AudioManager) getSystemService(Context.AUDIO_SERVICE);
        tts = new TextToSpeech(this, status -> {
            log("TTS init status=" + status + " (0 = OK)");
            if (status == TextToSpeech.SUCCESS) {
                int r = tts.setLanguage(new Locale("en", "IN"));
                if (r < 0) tts.setLanguage(Locale.ENGLISH);
                tts.setAudioAttributes(new AudioAttributes.Builder()
                        .setUsage(AudioAttributes.USAGE_VOICE_COMMUNICATION)
                        .setContentType(AudioAttributes.CONTENT_TYPE_SPEECH).build());
                tts.setOnUtteranceProgressListener(new UtteranceProgressListener() {
                    @Override public void onStart(String id) { log("TTS speaking " + id); }
                    @Override public void onError(String id) { log("TTS ERROR " + id); h.post(hangup); }
                    @Override public void onDone(String id) {
                        if ("m2".equals(id)) h.post(hangup);
                    }
                });
                ttsReady = true;
            }
        });
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        NotificationChannel ch = new NotificationChannel("cr", "CallResponder", NotificationManager.IMPORTANCE_LOW);
        ((NotificationManager) getSystemService(NOTIFICATION_SERVICE)).createNotificationChannel(ch);
        Notification n = new Notification.Builder(this, "cr")
                .setContentTitle("CallResponder is running")
                .setContentText("Unknown callers will be answered with your message")
                .setSmallIcon(android.R.drawable.sym_action_call)
                .build();
        if (Build.VERSION.SDK_INT >= 29) {
            startForeground(1, n, ServiceInfo.FOREGROUND_SERVICE_TYPE_SPECIAL_USE);
        } else {
            startForeground(1, n);
        }
        if (listener == null) {
            listener = new PhoneStateListener() {
                @Override
                public void onCallStateChanged(int state, String number) {
                    handleState(state, number);
                }
            };
            tm.listen(listener, PhoneStateListener.LISTEN_CALL_STATE);
        }
        return START_STICKY;
    }

    void handleState(int state, String number) {
        if (state == TelephonyManager.CALL_STATE_RINGING) {
            if (number != null && !number.isEmpty()) lastNumber = number;
            if (!scheduled) {
                scheduled = true;
                h.postDelayed(answerTask, ANSWER_DELAY_MS);
            }
        } else if (state == TelephonyManager.CALL_STATE_OFFHOOK) {
            log("Call connected, weAnswered=" + weAnswered);
            if (weAnswered) {
                h.postDelayed(this::speakMessage, 800);
                h.postDelayed(hangup, MAX_CALL_MS);
            }
        } else if (state == TelephonyManager.CALL_STATE_IDLE) {
            h.removeCallbacks(answerTask);
            h.removeCallbacks(hangup);
            scheduled = false;
            weAnswered = false;
            lastNumber = "";
            if (tts != null) tts.stop();
            restoreAudio();
        }
    }

    void speakMessage() {
        if (!weAnswered || !ttsReady) {
            log("Cannot speak: answered=" + weAnswered + " ttsReady=" + ttsReady);
            return;
        }
        try {
            if (Build.VERSION.SDK_INT >= 31) {
                boolean set = false;
                for (AudioDeviceInfo d : am.getAvailableCommunicationDevices()) {
                    if (d.getType() == AudioDeviceInfo.TYPE_BUILTIN_SPEAKER) {
                        set = am.setCommunicationDevice(d);
                        break;
                    }
                }
                log("Speaker route set=" + set);
            } else {
                am.setSpeakerphoneOn(true);
            }
            savedMusicVol = am.getStreamVolume(AudioManager.STREAM_MUSIC);
            am.setStreamVolume(AudioManager.STREAM_MUSIC, am.getStreamMaxVolume(AudioManager.STREAM_MUSIC), 0);
            am.setStreamVolume(AudioManager.STREAM_VOICE_CALL, am.getStreamMaxVolume(AudioManager.STREAM_VOICE_CALL), 0);
            log("Audio mode=" + am.getMode() + " speakerOn=" + am.isSpeakerphoneOn());
        } catch (Exception e) {
            log("Audio setup error: " + e.getMessage());
        }
        String text = getSharedPreferences(MainActivity.PREFS, MODE_PRIVATE)
                .getString(MainActivity.KEY_MSG, MainActivity.DEFAULT_MSG);
        Bundle p = new Bundle();
        int rc = tts.speak(text, TextToSpeech.QUEUE_FLUSH, p, "m1");
        log("speak() result=" + rc + " (0 = OK)");
        tts.playSilentUtterance(700, TextToSpeech.QUEUE_ADD, "gap");
        tts.speak(text, TextToSpeech.QUEUE_ADD, p, "m2");
    }

    void endCallNow() {
        try {
            if (weAnswered) telecom.endCall();
        } catch (Exception ignored) { }
    }

    void restoreAudio() {
        try {
            if (Build.VERSION.SDK_INT >= 31) am.clearCommunicationDevice();
            else am.setSpeakerphoneOn(false);
            if (savedMusicVol >= 0) am.setStreamVolume(AudioManager.STREAM_MUSIC, savedMusicVol, 0);
            savedMusicVol = -1;
        } catch (Exception ignored) { }
    }

    void sendSmsOnce(String number) {
        try {
            android.content.SharedPreferences sp = getSharedPreferences(MainActivity.PREFS, MODE_PRIVATE);
            if (!sp.getBoolean(MainActivity.KEY_SMS_ON, true)) return;
            if (number == null) return;
            String digits = number.replaceAll("[^0-9+]", "");
            if (digits.length() < 10) return;
            String today = new SimpleDateFormat("yyyy-MM-dd", Locale.US).format(new Date());
            String key = "sms_" + digits;
            if (today.equals(sp.getString(key, ""))) { log("SMS already sent today to " + digits); return; }
            String text = sp.getString(MainActivity.KEY_SMS, MainActivity.DEFAULT_SMS);
            SmsManager sm = SmsManager.getDefault();
            sm.sendMultipartTextMessage(digits, null, sm.divideMessage(text), null, null);
            sp.edit().putString(key, today).apply();
            log("SMS sent to " + digits);
        } catch (Exception e) {
            log("SMS ERROR: " + e.getMessage());
        }
    }

    boolean isContact(String number) {
        if (number == null || number.isEmpty()) return false;
        Uri uri = Uri.withAppendedPath(ContactsContract.PhoneLookup.CONTENT_FILTER_URI, Uri.encode(number));
        try (Cursor c = getContentResolver().query(uri,
                new String[]{ContactsContract.PhoneLookup._ID}, null, null, null)) {
            return c != null && c.moveToFirst();
        } catch (Exception e) {
            return true; // when unsure, do not answer
        }
    }

    // ---- simple log ----
    void log(String line) { appendLog(this, line); }

    static synchronized void appendLog(Context c, String line) {
        try (FileWriter w = new FileWriter(new File(c.getFilesDir(), "log.txt"), true)) {
            w.write(new SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.US).format(new Date()) + "  " + line + "\n");
        } catch (Exception ignored) { }
    }

    static synchronized String readLog(Context c) {
        File f = new File(c.getFilesDir(), "log.txt");
        if (!f.exists()) return "No calls logged yet.";
        ArrayList<String> lines = new ArrayList<>();
        String today = new SimpleDateFormat("yyyy-MM-dd", Locale.US).format(new Date());
        int todayCount = 0;
        try (BufferedReader r = new BufferedReader(new FileReader(f))) {
            String s;
            while ((s = r.readLine()) != null) {
                lines.add(s);
                if (s.startsWith(today) && s.contains("ANSWERED")) todayCount++;
            }
        } catch (Exception ignored) { }
        Collections.reverse(lines);
        StringBuilder sb = new StringBuilder("Answered today: " + todayCount + "\n\n");
        int max = Math.min(lines.size(), 300);
        for (int i = 0; i < max; i++) sb.append(lines.get(i)).append("\n");
        return sb.toString();
    }

    @Override
    public void onDestroy() {
        if (listener != null) tm.listen(listener, PhoneStateListener.LISTEN_NONE);
        h.removeCallbacksAndMessages(null);
        if (tts != null) tts.shutdown();
        super.onDestroy();
    }

    @Override public IBinder onBind(Intent i) { return null; }
}
