import { defineCollection, z } from "astro:content";

const posts = defineCollection({
  type: "content",
  schema: z.object({
    title: z.string(),
    date: z.string(),
    description: z.string().optional(),
    // slug is reserved by Astro — not declared in schema
  }),
});

export const collections = { posts };
