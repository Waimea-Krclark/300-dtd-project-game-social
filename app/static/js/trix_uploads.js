
document.addEventListener("trix-file-accept", e => {
    if (!e.file.type.startsWith("image/")) e.preventDefault();
});

document.addEventListener("trix-attachment-add", async e => {
    const attachment = e.attachment;
    if (!attachment.file) return;

    const fd = new FormData();
    fd.append("file", attachment.file);

    const res = await fetch("/upload-image", { method: "POST", body: fd });
    const { url } = await res.json();

    attachment.setAttributes({ url, href: url });
});