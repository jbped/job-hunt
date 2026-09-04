import {
  Bubble,
  BubbleContent,
  Message,
  MessageAvatar,
  MessageContent,
  MessageFooter,
  MessageGroup,
  MessageHeader,
} from "job-hunt-ui";

export const CompanionThread = () => (
  <MessageGroup style={{ maxWidth: 460 }}>
    <Message align="end">
      <MessageContent>
        <Bubble variant="secondary">
          <BubbleContent>
            What should I do next on the Initech application?
          </BubbleContent>
        </Bubble>
      </MessageContent>
    </Message>
    <Message>
      <MessageAvatar style={{ height: 32, fontSize: 12, fontWeight: 600 }}>
        JH
      </MessageAvatar>
      <MessageContent>
        <MessageHeader>Companion</MessageHeader>
        <Bubble>
          <BubbleContent>
            The resume is rendered but the cover letter is still a scaffold.
            Draft it and you're ready to submit.
          </BubbleContent>
        </Bubble>
        <MessageFooter>Just now</MessageFooter>
      </MessageContent>
    </Message>
  </MessageGroup>
);

export const Alignment = () => (
  <MessageGroup style={{ maxWidth: 460 }}>
    <Message align="start">
      <MessageAvatar style={{ height: 32, fontSize: 12, fontWeight: 600 }}>
        JH
      </MessageAvatar>
      <MessageContent>
        <Bubble>
          <BubbleContent>Aligned to the start — the companion.</BubbleContent>
        </Bubble>
      </MessageContent>
    </Message>
    <Message align="end">
      <MessageContent>
        <Bubble variant="secondary">
          <BubbleContent>Aligned to the end — you.</BubbleContent>
        </Bubble>
      </MessageContent>
    </Message>
  </MessageGroup>
);
