const encoder = new TextEncoder();
const decoder = new TextDecoder();

async function deriveKey(password, salt) {
    const baseKey = await crypto.subtle.importKey(
        "raw", encoder.encode(password), "PBKDF2", false, ["deriveKey"]
    );
    return crypto.subtle.deriveKey(
        { name: "PBKDF2", salt: salt, iterations: 250000, hash: "SHA-256" }, baseKey, { name: "AES-GCM", length: 256 }, false, ["encrypt", "decrypt"]
    );
}

async function encryptData(key, data) {
    const iv = crypto.getRandomValues(new Uint8Array(12));
    const encrypted = await crypto.subtle.encrypt({ name: "AES-GCM", iv }, key, data);
    return { iv, encrypted };
}

async function decryptData(key, iv, data) {
    return crypto.subtle.decrypt({ name: "AES-GCM", iv }, key, data);
}

const fileInput = document.getElementById('fileInput');
const fileLabel = document.querySelector('.custom-file-label');
const form      = document.getElementById('uploadForm');
const keyInput  = document.getElementById('keyInput');

fileInput.addEventListener('change', () => {
    let filePathDisplay = document.getElementById("filePathDisplay");
    if (!filePathDisplay) {
        filePathDisplay = document.createElement("div");
        filePathDisplay.id = "filePathDisplay";
        form.appendChild(filePathDisplay);
    }

    if (fileInput.files.length) {
        filePathDisplay.textContent = fileInput.files[0].webkitRelativePath || fileInput.files[0].name;
    } else {
        filePathDisplay.textContent = "";
    }
});

form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const password = keyInput.value;
    const file     = fileInput.files[0];
    if (!file) return alert("No file selected");

    try {
        const salt      = crypto.getRandomValues(new Uint8Array(16));
        const key       = await deriveKey(password, salt);
        const fileBytes = new Uint8Array(await file.arrayBuffer());
        const nameBytes = encoder.encode(file.name);
        const encName   = await encryptData(key, nameBytes);
        const encFile   = await encryptData(key, fileBytes);
        const combined  = new Uint8Array(salt.length + encName.iv.length + encName.encrypted.byteLength + 1 + encFile.iv.length + encFile.encrypted.byteLength);
        let offset      = 0;

        combined.set(salt, offset); offset += salt.length;
        combined.set(encName.iv, offset); offset += encName.iv.length;
        combined.set(new Uint8Array(encName.encrypted), offset); offset += encName.encrypted.byteLength;
        combined[offset++] = 0;
        combined.set(encFile.iv, offset); offset += encFile.iv.length;
        combined.set(new Uint8Array(encFile.encrypted), offset);

        const blob       = new Blob([combined]);
        const formData   = new FormData();
        const randomName = `file_${Date.now()}.dat`;

        formData.append("file", blob, randomName);

        const res = await fetch("/", { method: "POST", body: formData });

        if (!res.ok) throw new Error("Upload failed");
        fileLabel.textContent = `📄 File Encrypted ${document.querySelectorAll('.download-btn').length + 1}`;
        location.reload();
    } catch (err) {
        alert("Upload failed: " + err.message);
        console.error(err);
    }
});

document.querySelectorAll(".download-btn").forEach(btn => {
    btn.addEventListener("click", async () => {
        const password = prompt("Enter decryption key");
        if (!password) return;
        const fileName = btn.dataset.file;

        try {
            const res       = await fetch(`/download/${fileName}`, { credentials: "same-origin" });

            if (!res.ok) return alert("Download failed.");

            const data      = new Uint8Array(await res.arrayBuffer());
            let offset      = 0;
            const salt      = data.slice(offset, offset + 16); offset += 16;
            const key       = await deriveKey(password, salt);
            const nameIv    = data.slice(offset, offset + 12); offset += 12;
            const nameEnd   = data.indexOf(0, offset);
            const encName   = data.slice(offset, nameEnd);
            offset          = nameEnd + 1;
            const fileIv    = data.slice(offset, offset + 12); offset += 12;
            const encFile   = data.slice(offset);
            const nameBytes = await decryptData(key, nameIv, encName);
            const fileBytes = await decryptData(key, fileIv, encFile);
            const filename  = decoder.decode(nameBytes);
            const blob      = new Blob([fileBytes]);
            const url       = URL.createObjectURL(blob);
            const a         = document.createElement("a");
            a.href          = url;
            a.download      = filename;

            a.click();
            URL.revokeObjectURL(url);
            await fetch(`/delete/${fileName}`, { method: "POST", credentials: "same-origin" });

        } catch (err) {
            alert("Decryption failed");
            console.error(err);
        }
    });
});