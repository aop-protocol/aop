# AOP Landing Page

Professional landing page for the Agentic Observability Protocol (AOP).

## Features

- **Modern Design** - Clean, professional design with strategic use of brand colors
- **Smooth Animations** - GSAP-powered animations including scroll triggers, parallax, and counters
- **Fully Responsive** - Mobile-first design that works on all devices
- **Next.js 14** - Built with the latest Next.js App Router
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Utility-first styling with custom AOP color palette
- **shadcn/ui** - Beautiful, accessible UI components

## Sections

1. **Hero** - Animated gradient logo with cycling tagline (TRANSPARENT → AUDITABLE → ACTIONABLE)
2. **Impact** - OBSERVE/AUDIT/REPORT value proposition
3. **MCP Integration Hub** - Interactive tabs with documentation, API reference, examples, and quick start
4. **Live Demo** - YouTube video placeholder + real-time event table simulation
5. **Features Scroll** - Horizontal scrolling showcase of 4 key features
6. **Why AOP** - Animated stats: <1ms latency, 3 protocols, 100% privacy, 0 dependencies
7. **Upcoming Features** - HIPAA, GDPR, MCP Packages, A2A, AP2, and more
8. **Contact Developer** - Email, LinkedIn, and GitHub links for Ajit Singh
9. **Footer** - Links, resources, and social media

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn

### Installation

```bash
cd landing-page
npm install
```

### Development

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to view the landing page.

### Build

```bash
npm run build
```

This creates an optimized production build in the `.next` folder.

### Export Static Site

```bash
npm run build
npm run export
```

This creates a static export in the `out` folder that can be deployed to any static hosting service.

## Project Structure

```
landing-page/
├── src/
│   ├── app/
│   │   ├── layout.tsx      # Root layout with metadata
│   │   ├── page.tsx        # Main page component
│   │   └── globals.css     # Global styles and gradient utilities
│   ├── components/
│   │   ├── ui/
│   │   │   └── button.tsx  # Reusable button component
│   │   ├── Hero.tsx
│   │   ├── ImpactSection.tsx
│   │   ├── MCPTabs.tsx
│   │   ├── LiveDemo.tsx
│   │   ├── FeaturesScroll.tsx
│   │   ├── WhyAOP.tsx
│   │   ├── UpcomingFeatures.tsx
│   │   ├── ContactDeveloper.tsx
│   │   └── Footer.tsx
│   └── lib/
│       ├── utils.ts        # Utility functions
│       └── animations.ts   # GSAP animation helpers
├── public/
│   └── screenshots/        # Feature screenshots (add your images here)
├── tailwind.config.ts      # Tailwind config with AOP colors
├── tsconfig.json
└── package.json
```

## Color Palette

The landing page uses the official AOP color palette:

- **Charcoal** (#212121) - Primary dark
- **Mint** (#CAF9D5) - Light accent
- **Green** (#3ACF69) - Primary brand color
- **Gold** (#FEB727) - Accent
- **Purple** (#D664DE) - Accent
- **Gray** (#6C6C6A) - Neutral
- **Beige** (#C8B187) - Neutral accent
- **Red** (#BE3329) - Error/warning
- **Turquoise** (#6BD5C9) - Interactive elements
- **Indigo** (#505DD8) - Secondary brand

Colors are used minimally and strategically, following the design philosophy of the Tesoro XP website.

## Adding Screenshots

Place your feature screenshots in the `public/screenshots/` folder with the following names:

- `dashboard-table.png`
- `trace-viz.png`
- `analytics.png`
- `cli.png`

Then uncomment the `<Image>` components in [FeaturesScroll.tsx](src/components/FeaturesScroll.tsx).

## Adding YouTube Video

Replace the placeholder in [LiveDemo.tsx](src/components/LiveDemo.tsx) with your YouTube embed:

```tsx
<iframe
  src="https://www.youtube.com/embed/YOUR_VIDEO_ID"
  className="absolute inset-0 w-full h-full"
  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
  allowFullScreen
/>
```

## Customization

### Update Contact Info

Edit [ContactDeveloper.tsx](src/components/ContactDeveloper.tsx) to update:
- Email address
- LinkedIn URL
- GitHub URL

### Update Links

Edit [Footer.tsx](src/components/Footer.tsx) to update documentation and resource links.

### Modify Colors

Update [tailwind.config.ts](tailwind.config.ts) to change the color palette.

### Adjust Animations

Edit [src/lib/animations.ts](src/lib/animations.ts) to customize GSAP animations.

## Deployment

### Vercel (Recommended)

```bash
npm install -g vercel
vercel
```

### Static Export

```bash
npm run build
# Deploy the 'out' folder to:
# - GitHub Pages
# - Netlify
# - Cloudflare Pages
# - AWS S3
```

## Technologies

- **Framework:** Next.js 14 (App Router)
- **Language:** TypeScript
- **Styling:** Tailwind CSS
- **Components:** shadcn/ui
- **Animations:** GSAP 3.12+
- **Icons:** Lucide React

## Performance

- Optimized images (use Next.js Image component)
- Code splitting (automatic with Next.js)
- Lazy loading components
- Minimal JavaScript bundle
- Fast page loads (<2s FCP)

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)
- Mobile browsers (iOS Safari, Chrome Mobile)

## License

MIT License - see main [LICENSE](../LICENSE) file for details.

## Author

**Ajit Singh**
- Email: asing349@ucr.edu
- LinkedIn: [linkedin.com/in/ajitsingh](https://linkedin.com/in/ajitsingh)
- GitHub: [github.com/ajitsingh](https://github.com/ajitsingh)

---

Built with ❤️ for the AOP community
