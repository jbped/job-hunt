import {
  Button,
  Empty,
  EmptyContent,
  EmptyDescription,
  EmptyHeader,
  EmptyTitle,
} from "job-hunt-ui";

export const NoApplications = () => (
  <Empty style={{ maxWidth: 420 }}>
    <EmptyHeader>
      <EmptyTitle>No applications yet</EmptyTitle>
      <EmptyDescription>
        Capture a posting from your browser, or add one by hand. Everything
        about a role — the posting, your analysis, drafts and people — lives on
        its application.
      </EmptyDescription>
    </EmptyHeader>
    <EmptyContent>
      <Button>Add an application</Button>
    </EmptyContent>
  </Empty>
);

export const NoEvidence = () => (
  <Empty style={{ maxWidth: 420 }}>
    <EmptyHeader>
      <EmptyTitle>This role is unexamined</EmptyTitle>
      <EmptyDescription>
        We imported Acme (2019–2022) from your old resume, but nothing has been
        interviewed yet. An interview turns it into evidence your resumes can
        draw on.
      </EmptyDescription>
    </EmptyHeader>
    <EmptyContent>
      <Button>Interview me about Acme</Button>
    </EmptyContent>
  </Empty>
);
