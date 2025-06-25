# Project Overview
This iOS app empowers individuals aiming to reduce or eliminate alcohol consumption by offering a data-driven accountability tool focused on tracking sobriety streaks, financial savings, and health milestones. Tailored for those struggling with alcohol dependence, it simplifies progress visualization through a scrollable calendar interface (inspired by GitHub’s activity graph) where daily tiles log sobriety status or drink counts. Core features include real-time timers for sobriety duration, customizable savings trackers tied to alcohol expenses, milestone badges for motivation (e.g., 7 days sober), and a personal "why" section for grounding users in their goals.

# User stories

1. As a user, I want to create an account so that my sobriety data can be preserved if I delete and reinstall the app.
2. As a user, I want to view a calendar-style activity graph (like github activity graph) on the main screen so I can visualize my sobriety progress at a glance.
3. as a user i should see consecutive sober days become a darker color in the ui indicating my sober streak.
4. As a user, I want to mark each day as either sober or not sober by tapping on calendar tiles so I can track my progress.
5. As a user, I want to see my current streak of consecutive sober days so I can stay motivated to maintain it.
6. As a user, I want to view an active timer showing how long I've been sober in days, hours, and minutes so I can see my real-time progress.
7. As a user, i want to see the timer reset if Im not sober that day which breaks the streak
8. As a user, I want to input the cost of my typical drink so the app can calculate my financial savings.
9. As a user, I want to see how much money I've saved by not drinking so I can be motivated by the financial benefits.
10. As a user, I want to log the number of drinks I consumed on non-sober days so I can track my consumption patterns.
11. As a user, I want to log in with my credentials so I can access my sobriety data  in case I need to reinstall the app.
12. As a user, I want to see a single stat to show how much money I'ved saved based on a calculation of how much a single drink costs and an average of how drinks I have per week
13. As a user I want to see a single stat showing the current streak count
14. As a user I want to see another stat showing my longest streak count
15. As a user, I want the app to continue tracking my timer in the background so that the timer remains accurate even when I'm not using the app.
16. As a user, I want to tap on a calendar day to mark it as “sober” and have the day’s color update immediately on a scale from 1–10, so I receive instant visual confirmation of my progress.
17. As a user, I want the darkness of the day to reflect my consecutive streak (with a darker shade indicating a longer streak), so I can quickly assess my ongoing progress.
18. As a user, I want to be able to undo or correct a mistaken entry by tapping a day again, ensuring the calendar accurately reflects my progress.
19. As a user, I want the current day to be visually distinguished (e.g., outlined or labeled), so I can easily identify and update today’s status.
20. As a user, I want to scroll vertically through a continuous calendar grid that seamlessly merges weeks from different months without any gaps, so that I can effortlessly review my past, current, and upcoming days in a coherent, uninterrupted view.
21. As a user, I want to be able to share my current streak what will be shown as a graphic of the calendar activity of the sober days so I can share my progress with my close friends and family

# Tech Stack (stable versions)
Frontend
- React Native
- Expo
- Expo Router
- Tailwind CSS via Nativewind
- React Hook Form
- Zod
- react-native-async-storage
- expo-secure-store
- react-native-reusables

Backend
- Supabase

Languages
- TypeScript

Development Tools:
- Expo CLI
- ESLint
- Prettier
- Babel

