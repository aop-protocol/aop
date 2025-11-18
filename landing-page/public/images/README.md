# Images Directory

Place your images here for use in the landing page.

## Current Image Needs

### Demo Video Placeholder
- **Filename**: `demo-placeholder.png` or `demo-placeholder.jpg`
- **Recommended size**: 1920x1080 (16:9 aspect ratio)
- **Used in**: LiveDemo component
- **Example usage**:
  ```tsx
  <Image
    src="/images/demo-placeholder.png"
    alt="Demo Coming Soon"
    width={1920}
    height={1080}
  />
  ```

## File Organization

- `/images/` - General images
- `/images/screenshots/` - App screenshots
- `/images/logos/` - Brand logos and icons
- `/images/placeholders/` - Placeholder images

## Best Practices

1. Use WebP format when possible for better performance
2. Provide both light and dark mode versions if needed
3. Optimize images before uploading (use tools like TinyPNG)
4. Use descriptive filenames (e.g., `aop-dashboard-screenshot.png`)
