import { Bubble, BubbleContent, BubbleGroup } from "job-hunt-ui";

export const Conversation = () => (
  <BubbleGroup style={{ maxWidth: 460 }}>
    <Bubble variant="secondary">
      <BubbleContent>
        Can you tailor my resume for the Globex frontend role?
      </BubbleContent>
    </Bubble>
    <Bubble>
      <BubbleContent>
        I can. Your Skill Matrix backs React, TypeScript and design systems for
        that posting — I'll draft from the Acme and Initech evidence.
      </BubbleContent>
    </Bubble>
  </BubbleGroup>
);

export const Variants = () => (
  <div style={{ display: "flex", flexDirection: "column", gap: 8, maxWidth: 420 }}>
    <Bubble><BubbleContent>Default</BubbleContent></Bubble>
    <Bubble variant="secondary"><BubbleContent>Secondary</BubbleContent></Bubble>
    <Bubble variant="muted"><BubbleContent>Muted</BubbleContent></Bubble>
    <Bubble variant="tinted"><BubbleContent>Tinted</BubbleContent></Bubble>
    <Bubble variant="outline"><BubbleContent>Outline</BubbleContent></Bubble>
  </div>
);
