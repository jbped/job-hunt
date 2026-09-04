# Building with job-hunt-ui

A shadcn/ui component library (Radix primitives, Tailwind v4 tokens) for a
local-first job-hunt application. Everything is exported from
`window.JobHuntUI`.

## Setup and wrapping

Most components need no provider. Four do — wrap only when you use them:

| Provider | Required by |
|---|---|
| `SidebarProvider` | every `Sidebar*` component |
| `TooltipProvider` | `Tooltip`, `TooltipTrigger`, `TooltipContent` |
| `MessageScrollerProvider` | every `MessageScroller*` component |
| `Toaster` | rendered once at the app root for `sonner` toasts |

Light and dark both ship. Dark mode is a `dark` class on a root ancestor —
`<div className="dark">` — not a media query, so you can show both themes on one
screen. Seven base colour palettes are compiled in and selected with a
`data-base-color` attribute on the root element (`mist` is the default and
applies with no attribute; the others are `neutral`, `stone`, `zinc`, `taupe`,
`mauve`, `olive`).

## The styling idiom

Compose from the library's components, and write your own layout glue with
Tailwind utility classes. **Only the utilities listed below are compiled into
the shipped stylesheet** — there is no Tailwind compiler at render time, so a
class outside these families silently does nothing. Stay inside them, or use an
inline `style` object.

Colours are semantic tokens, never raw palette values. Never write
`bg-slate-100` or `#fff`; write `bg-muted`.

| Family | Available values |
|---|---|
| Surfaces | `bg-background`, `bg-card`, `bg-popover`, `bg-muted`, `bg-accent`, `bg-primary`, `bg-secondary`, `bg-destructive`, `bg-sidebar`, `bg-transparent` |
| Text | `text-foreground`, `text-muted-foreground`, `text-card-foreground`, `text-popover-foreground`, `text-primary`, `text-primary-foreground`, `text-secondary-foreground`, `text-accent-foreground`, `text-destructive`, `text-sidebar-foreground` |
| Borders / rings | `border`, `border-border`, `border-input`, `border-transparent`, `border-{0,2,4}`, `border-{t,r,b,l}`, `ring-ring`, `ring-{1,2}`, `outline-none` |
| Radius | `rounded-{none,xs,sm,md,lg,xl,2xl,3xl,full}` |
| Shadow | `shadow-{none,xs,sm,md,lg,xl}` |
| Layout | `flex`, `inline-flex`, `grid`, `block`, `inline-block`, `hidden`, `contents`, `flex-{row,col,wrap,nowrap,1}`, `shrink-{0,1}`, `grow-{0,1}` |
| Alignment | `items-{start,center,end,baseline,stretch}`, `justify-{start,center,end,between,around,evenly}`, `self-{auto,start,center,end,stretch}` |
| Grid | `grid-cols-{1,2,3,4,5,6,12}`, `col-span-{1,2,3,4,5,6,full}` |
| Spacing | `gap-{0,1,2,3,4,5,6,8,10,12,16}`, `gap-{x,y}-*`, `{p,px,py,pt,pr,pb,pl}-{0,1,2,3,4,5,6,8,10,12,16}`, `{m,mx,my,mt,mr,mb,ml}-{…,auto}`, `space-{x,y}-{1,2,3,4,6,8}` |
| Sizing | `{w,h}-{full,fit,auto,px,screen}`, `{w,h}-{4,5,6,8,10,12,16,20,24,32,48,64}`, `size-{3,4,5,6,8,10,12,16}`, `min-{w,h}-0`, `max-w-{xs…7xl,full,none,prose}` |
| Type | `text-{xs,sm,base,lg,xl,2xl,3xl,4xl}`, `font-{normal,medium,semibold,bold}`, `leading-{none,tight,snug,normal,relaxed}`, `tracking-{tight,normal,wide}`, `text-{left,center,right}`, `truncate`, `line-clamp-{1,2,3,4}`, `text-{balance,pretty}`, `break-words`, `whitespace-nowrap` |
| Position | `relative`, `absolute`, `fixed`, `sticky`, `static`, `{top,right,bottom,left,inset}-0`, `z-{0,10,20,30,40,50}` |
| Overflow | `overflow-{hidden,auto,visible}`, `overflow-{x,y}-{hidden,auto}` |
| Misc | `opacity-{0,50,60,70,80,90,100}`, `cursor-pointer`, `cursor-default`, `select-none`, `pointer-events-none`, `sr-only` |

`sm:`, `md:` and `lg:` prefixes are compiled for the display, flex-direction,
grid-column, gap and padding families.

## Where the truth lives

- `_ds/<folder>/styles.css` and its imports — the real token values and every
  compiled component rule. Read it before inventing a colour.
- `components/<group>/<Name>/<Name>.prompt.md` — per-component usage.
- `components/<group>/<Name>/<Name>.d.ts` — the exact props, including real
  variant unions.

## Composition rules worth knowing

- Components are **compound**. `Card` is a shell: real usage is
  `Card > CardHeader > CardTitle | CardDescription | CardAction`, then
  `CardContent` and `CardFooter`. The same shape applies to `Empty`, `Item`,
  `Field`, `InputGroup`, `Sidebar`, `Table`, `Message` and `Bubble`.
- Chat: `Message` is layout only. Put a `Bubble` inside `MessageContent` or it
  renders as bare text, and `align="end"` moves nothing.
- `Button` and `Badge` share one variant vocabulary: `default`, `secondary`,
  `outline`, `ghost`, `destructive`, `link`.
- Empty states should always offer the next action — the product rule is that no
  screen is a dead end.

## An idiomatic example

```jsx
const { Card, CardHeader, CardTitle, CardDescription, CardAction, CardContent,
        CardFooter, Badge, Button } = window.JobHuntUI;

<div className="grid gap-4 md:grid-cols-2 max-w-4xl">
  <Card>
    <CardHeader>
      <CardTitle>Senior Frontend Engineer</CardTitle>
      <CardDescription>Globex — Remote (US)</CardDescription>
      <CardAction><Badge>Interviewing</Badge></CardAction>
    </CardHeader>
    <CardContent>
      <p className="text-sm text-muted-foreground">
        Applied 12 days ago. Recruiter screen on Thursday.
      </p>
    </CardContent>
    <CardFooter className="gap-2">
      <Button size="sm">Open application</Button>
      <Button size="sm" variant="outline">Log an interview</Button>
    </CardFooter>
  </Card>
</div>
```
