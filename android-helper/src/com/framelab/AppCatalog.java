package com.framelab;

import android.content.Context;
import android.content.pm.ApplicationInfo;
import android.content.pm.PackageManager;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.drawable.Drawable;
import android.util.Base64;
import org.json.JSONArray;
import org.json.JSONObject;
import java.io.ByteArrayOutputStream;
import java.lang.reflect.Method;
import java.lang.reflect.Constructor;
import java.util.List;

/** Read-only catalog executed as the authorized ADB shell; no APK installation. */
public final class AppCatalog {
    public static void main(String[] args) throws Exception {
        Class<?> activityThread = Class.forName("android.app.ActivityThread");
        android.os.Looper.prepareMainLooper();
        Constructor<?> constructor = activityThread.getDeclaredConstructor();
        constructor.setAccessible(true);
        Object thread = constructor.newInstance();
        Method getSystemContext = activityThread.getDeclaredMethod("getSystemContext");
        getSystemContext.setAccessible(true);
        Context context = (Context) getSystemContext.invoke(thread);
        PackageManager pm = context.getPackageManager();
        List<ApplicationInfo> installed = pm.getInstalledApplications(0);
        JSONArray apps = new JSONArray();
        for (ApplicationInfo app : installed) {
            if (args.length > 0 && !java.util.Arrays.asList(args).contains(app.packageName)) continue;
            JSONObject row = new JSONObject();
            row.put("package", app.packageName);
            row.put("label", app.packageName);
            row.put("label_available", false);
            row.put("icon", JSONObject.NULL);
            try {
                CharSequence label = app.loadLabel(pm);
                if (label != null && label.length() > 0) {
                    row.put("label", label.toString());
                    row.put("label_available", true);
                }
            } catch (Exception ignored) { }
            try {
                Drawable drawable = app.loadIcon(pm);
                if (drawable != null) {
                    Bitmap bitmap = Bitmap.createBitmap(48, 48, Bitmap.Config.ARGB_8888);
                    drawable.setBounds(0, 0, 48, 48);
                    drawable.draw(new Canvas(bitmap));
                    ByteArrayOutputStream buffer = new ByteArrayOutputStream();
                    bitmap.compress(Bitmap.CompressFormat.PNG, 100, buffer);
                    row.put("icon", "data:image/png;base64," + Base64.encodeToString(buffer.toByteArray(), Base64.NO_WRAP));
                    bitmap.recycle();
                }
            } catch (Exception ignored) { }
            apps.put(row);
            if (apps.length() % 8 == 0) System.gc();
        }
        JSONObject result = new JSONObject();
        result.put("apps", apps);
        System.out.println(result.toString());
        System.exit(0);
    }
}
