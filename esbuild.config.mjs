import esbuild from "esbuild";

await esbuild.build({
    entryPoints: [
        "frontend/static/ts/login/login.ts",
        "frontend/static/ts/admin/admin.ts",
        "frontend/static/ts/reminders/reminders.ts",
        "frontend/static/ts/notificationservices/notificationservices.ts",
        "frontend/static/ts/settings/settings.ts"
    ],
    bundle: true,
    format: "esm",
    treeShaking: true,
    outdir: "frontend/static/js",
    entryNames: "[name]"
})
