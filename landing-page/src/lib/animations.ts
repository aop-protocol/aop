import { gsap } from "gsap"
import { ScrollTrigger } from "gsap/ScrollTrigger"

// Register GSAP plugins
if (typeof window !== "undefined") {
  gsap.registerPlugin(ScrollTrigger)
}

export const fadeInUp = (element: string | Element, delay = 0) => {
  return gsap.fromTo(
    element,
    {
      opacity: 0,
      y: 40,
    },
    {
      opacity: 1,
      y: 0,
      duration: 0.8,
      delay,
      ease: "power3.out",
    }
  )
}

export const fadeInScale = (element: string | Element, delay = 0) => {
  return gsap.fromTo(
    element,
    {
      opacity: 0,
      scale: 0.9,
    },
    {
      opacity: 1,
      scale: 1,
      duration: 0.6,
      delay,
      ease: "back.out(1.2)",
    }
  )
}

export const staggerFadeIn = (elements: string | Element[], delay = 0) => {
  return gsap.fromTo(
    elements,
    {
      opacity: 0,
      y: 30,
    },
    {
      opacity: 1,
      y: 0,
      duration: 0.6,
      stagger: 0.15,
      delay,
      ease: "power2.out",
    }
  )
}

export const scrollTriggerFade = (container: string | Element, elements: string | Element) => {
  return gsap.fromTo(
    elements,
    {
      opacity: 0,
      y: 50,
    },
    {
      opacity: 1,
      y: 0,
      duration: 1,
      stagger: 0.15,
      scrollTrigger: {
        trigger: container,
        start: "top 80%",
        end: "top 50%",
        toggleActions: "play none none reverse",
      },
    }
  )
}

export const numberCounter = (
  selector: string,
  start: number,
  target: number,
  duration = 2,
  prefix = '',
  suffix = ''
) => {
  const element = document.querySelector(selector)
  if (!element) return

  const obj = { val: start }
  return gsap.to(obj, {
    val: target,
    duration,
    ease: "power2.out",
    onUpdate: () => {
      element.textContent = `${prefix}${Math.round(obj.val)}${suffix}`
    },
  })
}

export const cycleText = (elements: HTMLElement[], duration = 3) => {
  let currentIndex = 0

  const cycle = () => {
    const current = elements[currentIndex]
    const next = elements[(currentIndex + 1) % elements.length]

    const tl = gsap.timeline()

    tl.to(current, {
      opacity: 0,
      scale: 0.95,
      y: -20,
      duration: 0.5,
      ease: "power2.in",
    })
    .set(current, { display: "none" })
    .set(next, { display: "inline-block", opacity: 0, scale: 0.95, y: 20 })
    .to(next, {
      opacity: 1,
      scale: 1,
      y: 0,
      duration: 0.5,
      ease: "power2.out",
    })

    currentIndex = (currentIndex + 1) % elements.length
  }

  // Initial setup
  elements.forEach((el, i) => {
    el.style.display = i === 0 ? "inline-block" : "none"
  })

  // Start cycling
  setInterval(cycle, duration * 1000)
}

export const horizontalScroll = (
  container: string | Element,
  items: NodeListOf<Element> | Element[]
) => {
  const itemsArray = Array.from(items)
  const totalWidth = itemsArray.length

  const tl = gsap.timeline({
    scrollTrigger: {
      trigger: container,
      start: "top top",
      end: () => `+=${window.innerHeight * 2}`,
      scrub: 1,
      pin: true,
    },
  })

  tl.to(itemsArray, {
    xPercent: -100 * (totalWidth - 1),
    ease: "none",
  })

  return tl
}

export const parallaxFloat = (
  element: string | Element,
  speed = 2,
  distance = 30
) => {
  return gsap.to(element, {
    y: `+=${distance}`,
    repeat: -1,
    yoyo: true,
    duration: speed,
    ease: "sine.inOut",
  })
}
