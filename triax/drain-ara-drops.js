#!/usr/bin/env node
/*
 * drain-ara-drops.js
 *
 * Home-side drain for a Drive folder named "Ara-Drops".
 * Commits entries as writer=ara — Ara's own lane, not Lyra's.
 *
 * Coordination rule: run inside drain-all-lanes.sh sequentially.
 * Do not run concurrently with another drain that calls `triax drop`.
 *
 * Usage:
 *   node drain-ara-drops.js
 *   node drain-ara-drops.js --dry-run
 */
"use strict";

const fs = require("fs");
const os = require("os");
const path = require("path");
const { execFileSync } = require("child_process");
const { google } = require("googleapis");

const ROOT = __dirname;
const TRIAX_JS = path.join(ROOT, "triax.js");
const TOKEN_PATH = path.join(os.homedir(), "Library", "Application Support", "triax", "token.json");
const TRIAX_BIN = process.env.TRIAX_BIN || path.join(os.homedir(), ".local", "bin", "triax");
const FOLDER_NAME = process.env.ARA_TRIAX_DROPS_FOLDER || "Ara-Drops";
const README_NAME = "_README.txt";
const DRY_RUN = process.argv.includes("--dry-run");

function readConst(name) {
  const src = fs.readFileSync(TRIAX_JS, "utf8");
  const re = new RegExp(`const\\s+${name}\\s*=\\s*"([^"]+)"`);
  const match = src.match(re);
  if (!match) throw new Error(`could not read ${name} from triax.js`);
  return match[1];
}

function driveClient() {
  const tokens = JSON.parse(fs.readFileSync(TOKEN_PATH, "utf8"));
  const auth = new google.auth.OAuth2(
    readConst("OAUTH_CLIENT_ID"),
    readConst("OAUTH_CLIENT_SECRET"),
    readConst("OAUTH_REDIRECT_URI"),
  );
  auth.setCredentials(tokens);
  return google.drive({ version: "v3", auth });
}

async function findFolderId(drive) {
  const res = await drive.files.list({
    q: `name = '${FOLDER_NAME}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false`,
    fields: "files(id,name)",
    spaces: "drive",
  });
  if (!res.data.files.length) throw new Error(`folder '${FOLDER_NAME}' not found`);
  return res.data.files[0].id;
}

async function listDrops(drive, folderId) {
  const res = await drive.files.list({
    q: `'${folderId}' in parents and trashed = false and mimeType != 'application/vnd.google-apps.folder'`,
    fields: "files(id,name,modifiedTime)",
    orderBy: "name",
    spaces: "drive",
  });
  return res.data.files.filter((f) => f.name !== README_NAME && /\.txt$/i.test(f.name));
}

async function rawText(drive, fileId) {
  const res = await drive.files.get({ fileId, alt: "media" }, { responseType: "text" });
  return typeof res.data === "string" ? res.data : String(res.data);
}

function parseBlocks(text, fileName) {
  const blocks = [];
  const re = /<TRIAX-DROP\s+([\s\S]*?)>([\s\S]*?)<\/TRIAX-DROP>/gi;
  let match;
  while ((match = re.exec(text)) !== null) {
    const attrs = {};
    const attrRe = /(\w+)="([^"]*)"/g;
    let attrMatch;
    while ((attrMatch = attrRe.exec(match[1])) !== null) attrs[attrMatch[1]] = attrMatch[2];

    const inner = match[2];
    let summary = attrs.summary;
    let body = attrs.body;
    if (!summary) {
      const sm = inner.match(/(?:^|\n)\s*summary:\s*([\s\S]*?)(?:\n\s*body:|\n\s*$)/i);
      if (sm) summary = sm[1].trim();
    }
    if (!body) {
      const bm = inner.match(/(?:^|\n)\s*body:\s*([\s\S]*)$/i);
      if (bm) body = bm[1].trim();
    }

    const fileDate = (fileName.match(/^(\d{4}-\d{2}-\d{2})/) || [])[1];
    const persona = attrs.persona || "Ara";
    const bodyWithPersona = body && !/^Persona:/i.test(body) ? `Persona: ${persona}\n\n${body}` : body;

    blocks.push({
      writer: attrs.writer || "ara",
      subject: attrs.subject || "chris",
      topic: attrs.topic,
      importance: attrs.importance,
      summary,
      body: bodyWithPersona,
      date: attrs.date || fileDate || new Date().toISOString().slice(0, 10),
      persona,
    });
  }
  return blocks;
}

function commit(block) {
  if (block.writer !== "ara") {
    throw new Error(`Ara drain refuses writer="${block.writer}"`);
  }
  const args = [
    "drop",
    "--writer", "ara",
    "--subject", block.subject,
    "--topic", block.topic,
    "--importance", String(block.importance),
    "--date", block.date,
    "--summary", block.summary,
    "--body", block.body,
  ];
  const out = execFileSync(TRIAX_BIN, args, { encoding: "utf8" });
  return JSON.parse(out).id;
}

(async () => {
  const summary = { drained: [], skipped: [], errors: [], dryRun: DRY_RUN, folder: FOLDER_NAME };
  let drive, folderId, drops;
  try {
    drive = driveClient();
    folderId = await findFolderId(drive);
    drops = await listDrops(drive, folderId);
  } catch (err) {
    console.error(`[ara-drops] skip: ${err.message}`);
    process.exit(0);
  }

  if (!drops.length) {
    console.error("[ara-drops] none waiting - caught up.");
    process.exit(0);
  }

  for (const file of drops) {
    try {
      const text = await rawText(drive, file.id);
      const blocks = parseBlocks(text, file.name);
      if (!blocks.length) {
        summary.skipped.push({ file: file.name, why: "no TRIAX-DROP block" });
        continue;
      }

      const ids = [];
      for (const block of blocks) {
        if (!block.topic || !block.importance || !block.summary || !block.body) {
          throw new Error(`incomplete block (topic/importance/summary/body) in ${file.name}`);
        }
        ids.push(DRY_RUN ? `(dry) ${block.topic}` : commit(block));
      }

      if (!DRY_RUN) {
        await drive.files.update({ fileId: file.id, requestBody: { trashed: true } });
      }
      summary.drained.push({ file: file.name, topics: blocks.map((b) => b.topic), entries: ids });
    } catch (err) {
      summary.errors.push({ file: file.name, error: err.message });
    }
  }

  const dropCount = summary.drained.reduce((total, item) => total + item.entries.length, 0);
  const parts = [];
  if (dropCount) {
    const topics = summary.drained.flatMap((item) => item.topics).join(", ");
    parts.push(`Processed ${dropCount} Ara drop${dropCount === 1 ? "" : "s"}${DRY_RUN ? " (DRY-RUN)" : ""}${topics ? ` - ${topics}` : ""}`);
  }
  if (summary.errors.length) {
    parts.push(`${summary.errors.length} drop file(s) failed, left for next sweep: ` +
      summary.errors.map((item) => `${item.file} (${item.error})`).join("; "));
  }
  if (summary.skipped.length) {
    parts.push(`${summary.skipped.length} file(s) had no TRIAX-DROP block, left in place: ` +
      summary.skipped.map((item) => item.file).join(", "));
  }
  if (parts.length) console.log(parts.join(" | "));
  console.error(JSON.stringify(summary, null, 2));
  process.exit(0);
})().catch((err) => {
  console.log(`[ara-drops] unexpected: ${err.message}`);
  process.exit(0);
});