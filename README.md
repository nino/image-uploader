# Image uploader script for blog posts

The idea is:
I want to take a full-quality photo
and use this script to generate something like

```html
<a href="full-res-url">
    <img src="small-url" />
</a>
```

to put in a blog post.
The script should generate the smaller version of the file,
upload both versions to Backblaze B2,
and output the HTML snippet.

Execute with

```sh
uv run upload.py my-file-name
```
