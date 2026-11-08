"""Site content in one place.

Edit these lists to change what appears on the pages; the templates loop
over them, so you never have to touch HTML to add a project or a service.
"""

SERVICES = [
    {
        "icon": "phone",
        "title": "Mobile apps",
        "description": "Native iPhone and iPad apps that feel fast, polished and right at home on Apple devices.",
    },
    {
        "icon": "browser",
        "title": "Web apps",
        "description": "Responsive web applications, from sharp marketing sites to full products with accounts, dashboards and APIs.",
    },
    {
        "icon": "sparkle",
        "title": "AI integration",
        "description": "Assistants, smart search, automation and other AI features built into new or existing products.",
    },
    {
        "icon": "layers",
        "title": "UI/UX design",
        "description": "Interfaces people enjoy using: user flows, wireframes, interactive prototypes and design systems.",
    },
]

PROCESS = [
    {"title": "Discover", "description": "I dig into your idea, your users and your goals to define what success looks like."},
    {"title": "Design", "description": "Flows, wireframes and polished visuals, so you can see and feel the product before it is built."},
    {"title": "Build", "description": "Clean, tested code shipped in short cycles, with regular demos so you are never in the dark."},
    {"title": "Launch", "description": "App Store and web launch, monitoring and ongoing improvements once real users arrive."},
]

# Project categories used for the filter buttons on the Work page.
CATEGORIES = {
    "mobile": "Mobile",
    "web": "Web",
    "ai": "AI",
}

# Each project card. Set "status" to "live" and fill in "url" / "repo" when a
# project is ready to show; "coming_soon" cards get a placeholder visual.
# "theme" picks the card's colour scheme: "violet", "mint" or "lavender".
PROJECTS = [
    {
        "title": "Mobile app",
        "category": "mobile",
        "summary": "A native iPhone app currently in the studio. Full case study coming soon.",
        "tags": ["iOS", "Mobile"],
        "status": "coming_soon",
        "theme": "violet",
        "url": None,
        "repo": None,
    },
    {
        "title": "Web app",
        "category": "web",
        "summary": "A full-stack web application in development. Full case study coming soon.",
        "tags": ["Web", "Full-stack"],
        "status": "coming_soon",
        "theme": "lavender",
        "url": None,
        "repo": None,
    },
    {
        "title": "AI product",
        "category": "ai",
        "summary": "An AI-powered product taking shape. Full case study coming soon.",
        "tags": ["AI", "Automation"],
        "status": "coming_soon",
        "theme": "mint",
        "url": None,
        "repo": None,
    },
]

TOOLKIT = [
    "Swift", "SwiftUI", "Python", "Flask", "JavaScript", "TypeScript",
    "React", "Next.js", "Tailwind CSS", "LLM APIs", "Figma", "Git & GitHub",
]

# Options for the "What can we help with?" dropdown on the contact form.
PROJECT_TYPES = [
    ("mobile", "Mobile app"),
    ("web", "Web app"),
    ("ai", "AI integration"),
    ("design", "UI/UX design"),
    ("other", "Something else"),
]

SOCIAL_LINKS = [
    {"label": "GitHub", "url": "https://github.com/VieiraStudios"},
]
