## [1.1.0] — 2026-06-16

### 🛠 What Was Requested

> The landing page text containers were centered instead of left-aligned. The navbar elements were bunched together in the middle instead of being distributed across the full navbar width.

### ✅ What Was Changed

- **Navbar** ([`Navbar.jsx`](src/components/Navbar.jsx)): Removed `max-w-7xl` centered container. Logo is now pinned to the far left, nav links are absolutely centered, and auth buttons (Officer Login + Create Account) are pinned to the far right — spanning the full viewport width.
- **Home page** ([`Home.jsx`](src/pages/Home.jsx)): Replaced all `max-w-7xl mx-auto` containers with full-width `w-full px-6 lg:px-10 xl:px-16` containers so the hero, Core Modules, Why AI Matters, and CTA sections fill the screen edge to edge.
- **Footer** ([`Footer.jsx`](src/components/Footer.jsx)): Same container fix applied so footer columns also span the full width.
- **All other pages** ([`Blog.jsx`](src/pages/Blog.jsx), [`Videos.jsx`](src/pages/Videos.jsx), [`About.jsx`](src/pages/About.jsx), [`Pricing.jsx`](src/pages/Pricing.jsx), [`FAQ.jsx`](src/pages/FAQ.jsx), [`Contact.jsx`](src/pages/Contact.jsx)): Applied consistent full-width container treatment.

---

## [1.0.0] — 2026-06-16


### 📋 What Was Requested

> Build the AAAT (American Academy of Advanced Thinking) website based on the provided UI/UX design files in `/UI/UX/`. Use React and Tailwind CSS. Use logo and images from `/UI/UX/assets/` folder. Maintain a README file and a CHANGELOG documenting all changes.

---

### ✅ What Was Built

#### Project Setup
- Initialized **React + Vite** project from scratch in `/Users/HMZiyad/projects/charisma/`
- Configured **Tailwind CSS v3** with PostCSS
- Added **React Router DOM v6** for client-side routing
- Added **Lucide React** for icons
- Set up **Google Fonts (Inter)** for typography
- Created custom Tailwind config with `navy` color palette matching the design

#### Pages Created (12 total)

| File | Route | Based On Design |
|------|-------|-----------------|
| `src/pages/Home.jsx` | `/` | `Landing Pages/landing_page.png` |
| `src/pages/Pricing.jsx` | `/pricing` | `Landing Pages/pricing.png` |
| `src/pages/Blog.jsx` | `/blog` | `Landing Pages/blog.png` |
| `src/pages/Videos.jsx` | `/videos` | `Landing Pages/videos.png` |
| `src/pages/About.jsx` | `/about` | `Landing Pages/about.png` |
| `src/pages/FAQ.jsx` | `/faq` | `Landing Pages/FAQ.png` |
| `src/pages/Contact.jsx` | `/contact` | `Landing Pages/Contact.png` |
| `src/pages/Login.jsx` | `/login` | `Authentication/login.png` |
| `src/pages/SignUp.jsx` | `/signup` | `Authentication/create_new_account.png` |
| `src/pages/ForgotPassword.jsx` | `/forgot-password` | `Authentication/forgot_password.png` |
| `src/pages/OTPVerify.jsx` | `/verify-otp` | `Authentication/otp.png` |
| `src/pages/SetNewPassword.jsx` | `/reset-password` | `Authentication/set_new_password.png` |

#### Shared Components
- `src/components/Navbar.jsx` — Logo, nav links, Officer Login + Create Account buttons
- `src/components/Footer.jsx` — 4-column dark navy footer with Platform/Resources/Company links

#### Assets
- Copied from `UI/UX/assets/` to `public/assets/`:
  - `logo.png` — AAAT circular logo
  - `home.png` — Hero background (police officer with laptop at night)
  - `why_specialized_aI_matters.png` — Feature section image (officer at command center)

#### Design Decisions
- Auth pages (Login, Sign Up, Forgot Password, OTP, Set Password) are implemented as **full-page centered modal cards** matching the design (white card on gray background)
- **No images were generated** — only the provided assets were used
- FAQ accordion defaults first item to open, matching the design
- Contact form shows a success state after submission
- OTP inputs auto-advance focus to the next input on digit entry
- Premium Module Locked section on Pricing page is a static demo UI exactly as shown in the design

---

## Future Changes

*Future updates will be logged here.*
