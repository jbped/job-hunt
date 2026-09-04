import {
  Bubble,
  BubbleContent,
  BubbleGroup,
  Button,
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "job-hunt-ui";

export const CompanionDrawer = () => (
  <Sheet open>
    <SheetContent>
      <SheetHeader>
        <SheetTitle>Companion</SheetTitle>
        <SheetDescription>Scoped to Globex</SheetDescription>
      </SheetHeader>
      <div style={{ padding: "0 16px" }}>
        <BubbleGroup>
          <Bubble variant="secondary">
            <BubbleContent>What's left before I can submit?</BubbleContent>
          </Bubble>
          <Bubble>
            <BubbleContent>
              The cover letter is still a scaffold. I can draft it from your
              Acme evidence.
            </BubbleContent>
          </Bubble>
        </BubbleGroup>
        <Button style={{ marginTop: 12 }}>Draft the cover letter</Button>
      </div>
    </SheetContent>
  </Sheet>
);
