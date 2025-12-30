/* Copy web/dist -> public (clean) */
const fs = require("fs");
const path = require("path");

const dist = path.join(__dirname, "..", "web", "dist");
const pub = path.join(__dirname, "..", "public");

function rmrf(p) {
    if (!fs.existsSync(p)) return;
    fs.rmSync(p, { recursive: true, force: true });
}

function mkdirp(p) {
    fs.mkdirSync(p, { recursive: true });
}

function copyDir(src, dst) {
    mkdirp(dst);
    for (const entry of fs.readdirSync(src, { withFileTypes: true })) {
        const s = path.join(src, entry.name);
        const d = path.join(dst, entry.name);
        if (entry.isDirectory()) copyDir(s, d);
        else fs.copyFileSync(s, d);
    }
}

rmrf(pub);
mkdirp(pub);
copyDir(dist, pub);

console.log("Synced web/dist -> public");
