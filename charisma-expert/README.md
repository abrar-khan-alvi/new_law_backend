# KLYVOREK

AI-assisted law-enforcement documentation platform. Built with **React**, **Vite**, and **Tailwind CSS**.

---

## 🚀 Getting Started

### Prerequisites

- Node.js >= 18
- npm >= 9

### Installation

```bash
# 1. Navigate to the project directory
cd /path/to/charisma

# 2. Install all dependencies
npm install

# 3. Start the development server
npm run dev
```

The app will be available at **http://localhost:5173**

### Build for Production

```bash
npm run build
```

---

## 📂 Project Structure

```
charisma/
├── public/
│   └── assets/             # Static images (logo, hero photos)
│       ├── logo.png
│       ├── home.png
│       └── why_specialized_aI_matters.png
├── src/
│   ├── components/
│   │   ├── Navbar.jsx      # Shared navigation bar
│   │   └── Footer.jsx      # Shared footer
│   ├── pages/
│   │   ├── Home.jsx        # Landing page (/)
│   │   ├── Pricing.jsx     # Pricing page (/pricing)
│   │   ├── Blog.jsx        # Blog & resources (/blog)
│   │   ├── Videos.jsx      # Video library (/videos)
│   │   ├── About.jsx       # About page (/about)
│   │   ├── FAQ.jsx         # FAQ page (/faq)
│   │   ├── Contact.jsx     # Contact page (/contact)
│   │   ├── Login.jsx       # Login (/login)
│   │   ├── SignUp.jsx      # Sign Up (/signup)
│   │   ├── ForgotPassword.jsx  # Forgot password (/forgot-password)
│   │   ├── OTPVerify.jsx   # OTP verification (/verify-otp)
│   │   └── SetNewPassword.jsx  # Reset password (/reset-password)
│   ├── App.jsx             # Router configuration
│   ├── main.jsx            # React entry point
│   └── index.css           # Global styles + Tailwind directives
├── index.html              # HTML entry point
├── vite.config.js
├── tailwind.config.js
├── postcss.config.js
├── package.json
├── README.md               # This file
└── CHANGELOG.md            # Change history
```

---

## 🗺️ Pages & Routes

| Route | Page | Description |
|-------|------|-------------|
| `/` | Home | Hero, Core Modules, Why AI Matters, CTA |
| `/pricing` | Pricing | 3 plan tiers + Premium Module Locked example |
| `/blog` | Blog | Article grid with category filter & search |
| `/videos` | Videos | Video card library |
| `/about` | About | Mission, values grid, team section |
| `/faq` | FAQ | Accordion-style FAQ items |
| `/contact` | Contact | Contact info + contact form |
| `/login` | Login | Officer login modal |
| `/signup` | Sign Up | Create account modal |
| `/forgot-password` | Forgot Password | Email reset request |
| `/verify-otp` | OTP Verify | 5-digit code verification |
| `/reset-password` | Set New Password | New password form |

---

## 🎨 Tech Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| React | 18 | UI framework |
| Vite | 6 | Build tool & dev server |
| Tailwind CSS | 3 | Utility-first styling |
| React Router DOM | 6 | Client-side routing |
| Lucide React | latest | Icon library |

---

## 🖼️ Assets

All images are sourced from the provided UI/UX design folder and copied to `public/assets/`:
- `logo.png` — KLYVOREK circular logo (used throughout the public site and application)
- `home.png` — Hero background image (police officer with laptop)
- `why_specialized_aI_matters.png` — Feature section image (officer at workstation)

---

## 📋 Design Source

UI/UX designs are located in:
```
UI/UX/
├── Landing Pages/    # Home, Pricing, Blog, Videos, About, FAQ, Contact
├── Authentication/   # Login, Sign Up, Forgot Password, OTP, Set Password
└── assets/           # Logo and images
```
# charisma-expert-all 
