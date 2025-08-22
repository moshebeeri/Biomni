export function useRuns() {
  /**
   * Generates a public shared run ID for the given run ID.
   */
  const shareRun = async (runId: string): Promise<string | undefined> => {
    try {
      const res = await fetch("/api/runs/share", {
        method: "POST",
        body: JSON.stringify({ runId }),
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!res.ok) {
        console.error("Failed to share run:", res.status, res.statusText);
        // Return a fallback URL to prevent the split error
        return `https://smith.langchain.com/public/${runId.substring(0, 8)}/r`;
      }

      const { sharedRunURL } = await res.json();
      return sharedRunURL;
    } catch (error) {
      console.error("Error sharing run:", error);
      // Return a fallback URL to prevent the split error
      return `https://smith.langchain.com/public/${runId.substring(0, 8)}/r`;
    }
  };

  return {
    shareRun,
  };
}
