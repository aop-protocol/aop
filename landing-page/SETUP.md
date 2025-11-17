# AOP Landing Page - Quick Setup Guide

Get the AOP landing page running in under 5 minutes.

## Prerequisites

Ensure you have:
- **Node.js 18+** installed (`node --version`)
- **npm** or **yarn** installed

## Step 1: Install Dependencies

```bash
cd landing-page
npm install
```

This installs:
- Next.js 14
- React 18
- GSAP 3.12+ (animations)
- Tailwind CSS
- shadcn/ui components
- Lucide React icons
- TypeScript

## Step 2: Run Development Server

```bash
npm run dev
```

The landing page will be available at: **http://localhost:3000**

## Step 3: Customize Content (Optional)

### Add Screenshots

1. Add your feature screenshots to `public/screenshots/`:
   - `dashboard-table.png`
   - `trace-viz.png`
   - `analytics.png`
   - `cli.png`

2. Uncomment the `<Image>` component in `src/components/FeaturesScroll.tsx`:

```tsx
<Image
  src={feature.screenshot}
  alt={feature.title}
  fill
  className="object-cover"
/>
```

### Add YouTube Video

Replace the placeholder in `src/components/LiveDemo.tsx`:

```tsx
<iframe
  src="https://www.youtube.com/embed/YOUR_VIDEO_ID"
  className="absolute inset-0 w-full h-full"
  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
  allowFullScreen
/>
```

### Update Contact Information

Edit `src/components/ContactDeveloper.tsx` to update:
- Email: `asing349@ucr.edu`
- LinkedIn URL
- GitHub URL

## Step 4: Build for Production

```bash
npm run build
```

This creates an optimized build in `.next/`.

## Step 5: Deploy

### Option A: Vercel (Easiest)

```bash
npm install -g vercel
vercel
```

### Option B: Static Export

```bash
npm run build
# The static files will be in the 'out' folder
# Deploy to GitHub Pages, Netlify, Cloudflare Pages, etc.
```

### Option C: Self-Hosted

```bash
npm run build
npm start
```

## Troubleshooting

### Port Already in Use

If port 3000 is busy:
```bash
npm run dev -- -p 3001
```

### Build Errors

Clear cache and reinstall:
```bash
rm -rf node_modules .next
npm install
npm run build
```

### GSAP Not Animating

Ensure ScrollTrigger is properly loaded. Check browser console for errors.

### Images Not Loading

For static export, all images must be in the `public/` folder with unoptimized mode enabled (already configured in `next.config.js`).

## Project Structure

```
landing-page/
├── src/
│   ├── app/              # Next.js app directory
│   ├── components/       # React components
│   └── lib/              # Utilities and animations
├── public/               # Static assets
├── package.json
├── tailwind.config.ts
└── next.config.js
```

## Key Files to Edit

1. **Contact Info**: `src/components/ContactDeveloper.tsx`
2. **Footer Links**: `src/components/Footer.tsx`
3. **Screenshots**: `src/components/FeaturesScroll.tsx`
4. **YouTube Video**: `src/components/LiveDemo.tsx`
5. **Colors**: `tailwind.config.ts`
6. **Animations**: `src/lib/animations.ts`

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm start` - Start production server
- `npm run lint` - Run ESLint

## Need Help?

See the full [README.md](README.md) for detailed documentation.

---

**Ready to launch!** 🚀
