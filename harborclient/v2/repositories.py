from harborclient import base


class RepositoryManager(base.Manager):
    def get(self, id):
        """Get a Repository."""
        return self._get("/repositories/%s" % id)

    def list(self, project):
        """Get repositories accompany with relevant project and repo name."""
        repositories = self._list("/projects/%s/repositories" % project)
        return repositories

    def list_projects(self):
        return self._list("/projects")

    def delete_repository(self, repo_name):
        """Delete the repository."""
        return self.api.client.delete(
            "/repositories/%s" % repo_name)

    def list_tags(self, repo_name):
        """Get the tag of the repository."""
        return self.api.client.get(
            "/%s/tags/list" % repo_name)

    def delete_tags(self, repo_name, tag_name):
        """Delete the tag of the repository."""
        return self.api.client.delete(
            "/repositories/%s/tags/%s" % (repo_name, tag_name))

    def get_manifests(self, repo_name, tag):
        """Get manifests of a relevant repository."""
        return self.api.client.get(
            "/%(repo_name)s/manifests/%(tag)s"
            % {"repo_name": repo_name, "tag": tag})

    def get_top(self, count):
        """Get public repositories which are accessed most."""
        return self._list("/repositories/top?count=%s" % count)
