import { defineConfig } from "astro/config";

export default defineConfig({
  // Deployed to the root of the custom domain — no base path needed.
  site: "https://sterlingparis.com",
  output: "static",
});
