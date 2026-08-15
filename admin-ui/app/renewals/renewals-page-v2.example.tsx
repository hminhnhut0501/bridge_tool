import { renewalFixture } from "./renewal-contract";
import { RenewalsPageV2 } from "./renewals-page-v2";

export function RenewalPageContractExample() {
  return <RenewalsPageV2 view={renewalFixture("expiring-soon")} onRefresh={() => undefined} />;
}
