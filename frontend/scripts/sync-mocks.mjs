import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const fixturesDir = path.resolve(__dirname, "../../contracts/fixtures");
const mocksDir = path.resolve(__dirname, "../src/mocks");

if (!fs.existsSync(fixturesDir)) {
  console.error(`Fixtures directory not found: ${fixturesDir}`);
  process.exit(1);
}

if (!fs.existsSync(mocksDir)) {
  fs.mkdirSync(mocksDir, { recursive: true });
}

const files = fs.readdirSync(fixturesDir).filter((file) => file.endsWith(".json"));

if (files.length === 0) {
  console.warn("No fixture JSON files found to copy.");
}

for (const file of files) {
  const src = path.join(fixturesDir, file);
  const dest = path.join(mocksDir, file);
  fs.copyFileSync(src, dest);
  console.log(`Synced: ${file} -> src/mocks/${file}`);
}

console.log(`Successfully synced ${files.length} fixture files to src/mocks/`);

