import {
  Badge,
  Button,
  Item,
  ItemActions,
  ItemContent,
  ItemDescription,
  ItemGroup,
  ItemTitle,
} from "job-hunt-ui";

export const NextStepRow = () => (
  <Item style={{ maxWidth: 520 }}>
    <ItemContent>
      <ItemTitle>Draft the cover letter for Initech</ItemTitle>
      <ItemDescription>
        The resume is rendered and the analysis is written — the cover letter is
        the last thing missing before you submit.
      </ItemDescription>
    </ItemContent>
    <ItemActions>
      <Button size="sm">Draft it</Button>
    </ItemActions>
  </Item>
);

export const Variants = () => (
  <ItemGroup style={{ maxWidth: 520 }}>
    <Item variant="default">
      <ItemContent>
        <ItemTitle>Default</ItemTitle>
        <ItemDescription>No activity for 14 days.</ItemDescription>
      </ItemContent>
      <ItemActions>
        <Badge>Applied</Badge>
      </ItemActions>
    </Item>
    <Item variant="outline">
      <ItemContent>
        <ItemTitle>Outline</ItemTitle>
        <ItemDescription>Interview scheduled for Thursday.</ItemDescription>
      </ItemContent>
      <ItemActions>
        <Badge>Interviewing</Badge>
      </ItemActions>
    </Item>
    <Item variant="muted">
      <ItemContent>
        <ItemTitle>Muted</ItemTitle>
        <ItemDescription>Closed — position filled.</ItemDescription>
      </ItemContent>
      <ItemActions>
        <Badge>Closed</Badge>
      </ItemActions>
    </Item>
  </ItemGroup>
);
