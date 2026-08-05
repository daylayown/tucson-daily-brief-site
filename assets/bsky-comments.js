/* Bluesky-powered comments (SOCIAL-AUTOPOST.md Part 3).
 *
 * Each article page carries a hidden <section id="bsky-comments">. This script
 * looks up the page's canonical URL in /assets/bluesky-posts.json (exported by
 * social/bluesky_poster.py from its posting ledger), fetches that post's reply
 * thread from the public Bluesky AppView, and renders the replies. Pages with
 * no Bluesky post keep the section hidden. No backend, no build step.
 *
 * Dev override: append ?bsky-uri=at://did:plc:.../app.bsky.feed.post/rkey to
 * preview the section against any post's thread.
 */
(async function () {
  const section = document.getElementById("bsky-comments");
  if (!section) return;
  const metaEl = document.getElementById("bsky-comments-meta");
  const listEl = document.getElementById("bsky-comments-list");
  const linkEl = document.getElementById("bsky-comments-link");

  function fmtDate(iso) {
    const d = new Date(iso);
    if (isNaN(d)) return "";
    const opts = { month: "short", day: "numeric" };
    if (d.getFullYear() !== new Date().getFullYear()) opts.year = "numeric";
    return d.toLocaleDateString(undefined, opts);
  }

  function renderReply(node, depth) {
    const post = node.post;
    const author = post.author || {};
    const wrap = document.createElement("div");
    wrap.className = "bsky-comment" + (depth ? " bsky-comment--nested" : "");

    const head = document.createElement("p");
    head.className = "bsky-comment__author";
    if (author.avatar && /^https:\/\//.test(author.avatar)) {
      const img = document.createElement("img");
      img.className = "bsky-comment__avatar";
      img.src = author.avatar;
      img.alt = "";
      img.loading = "lazy";
      head.appendChild(img);
    }
    const name = document.createElement("a");
    name.className = "bsky-comment__name";
    name.href = "https://bsky.app/profile/" + encodeURIComponent(author.handle || author.did);
    name.target = "_blank";
    name.rel = "noopener nofollow";
    name.textContent = author.displayName || author.handle || "unknown";
    head.appendChild(name);
    const when = document.createElement("span");
    when.className = "bsky-comment__date";
    when.textContent = fmtDate((post.record || {}).createdAt || post.indexedAt);
    head.appendChild(when);
    wrap.appendChild(head);

    const body = document.createElement("p");
    body.className = "bsky-comment__text";
    body.textContent = (post.record || {}).text || "";
    wrap.appendChild(body);

    if (depth < 3) {
      children(node).forEach(function (child) {
        wrap.appendChild(renderReply(child, depth + 1));
      });
    }
    return wrap;
  }

  function children(node) {
    return (node.replies || [])
      .filter(function (r) {
        return r && r.post && r.post.record && !(r.post.labels || []).length;
      })
      .sort(function (a, b) {
        return new Date(a.post.record.createdAt) - new Date(b.post.record.createdAt);
      });
  }

  try {
    let uri = new URLSearchParams(location.search).get("bsky-uri");
    if (!uri) {
      const canonical = document.querySelector('link[rel="canonical"]');
      if (!canonical) return;
      const res = await fetch("/assets/bluesky-posts.json", { cache: "no-cache" });
      if (!res.ok) return;
      uri = (await res.json())[canonical.href];
      if (!uri) return;
    }
    const m = uri.match(/^at:\/\/([^/]+)\/app\.bsky\.feed\.post\/([a-z0-9]+)$/i);
    if (!m) return;
    linkEl.href = "https://bsky.app/profile/" + m[1] + "/post/" + m[2];

    const res = await fetch(
      "https://public.api.bsky.app/xrpc/app.bsky.feed.getPostThread" +
        "?depth=6&parentHeight=0&uri=" + encodeURIComponent(uri));
    if (!res.ok) return;
    const thread = (await res.json()).thread;
    if (!thread || !thread.post) return;

    const likes = thread.post.likeCount || 0;
    const reposts = thread.post.repostCount || 0;
    const bits = [];
    if (likes) bits.push(likes + (likes === 1 ? " like" : " likes"));
    if (reposts) bits.push(reposts + (reposts === 1 ? " repost" : " reposts"));
    metaEl.textContent = bits.length ? "This story has " + bits.join(" and ") + " on Bluesky." : "";

    const replies = children(thread);
    if (replies.length) {
      replies.forEach(function (r) { listEl.appendChild(renderReply(r, 0)); });
      linkEl.textContent = "Join the conversation on Bluesky";
    } else {
      linkEl.textContent = "Be the first to comment — reply on Bluesky";
    }
    section.hidden = false;
  } catch (err) {
    /* any failure: section simply stays hidden */
  }
})();
