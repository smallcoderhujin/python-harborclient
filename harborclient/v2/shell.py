from __future__ import print_function

import getpass
import logging
import re

from oslo_utils import strutils

import harborclient.exceptions
from harborclient import exceptions as exp
from harborclient import utils

logger = logging.getLogger(__name__)


def is_id(obj):
    try:
        int(obj)
        return True
    except ValueError:
        return False


@utils.arg(
    '--sortby',
    metavar='<sortby>',
    dest="sortby",
    default="user_id",
    help='Sort key.')
def do_user_list(cs, args):
    """Get registered users of Harbor."""
    try:
        users = cs.users.list()
    except exp.Forbidden as e:
        raise exp.CommandError(e.message)
    # Get admin user
    try:
        admin = cs.users.get(1)
        users.append(admin)
    except Exception:
        pass
    fields = ['user_id', 'username', 'is_admin',
              'email', 'realname', 'comment']
    formatters = {"is_admin": 'has_admin_role'}
    utils.print_list(users, fields, formatters=formatters, sortby=args.sortby)


@utils.arg(
    'user',
    metavar='<user>',
    help='User name or id')
def do_set_admin(cs, args):
    """Update a registered user to change to be an administrator of Harbor."""
    try:
        user = cs.users.find(args.user)
    except exp.NotFound:
        print("User '%s' not found." % args.user)
    cs.users.set_admin(user['user_id'], True)
    print("Set user '%s' as administrator successfully." % args.user)


@utils.arg(
    'user',
    metavar='<user>',
    help='User name or id')
def do_revoke_admin(cs, args):
    """Update a registered user to be a non-admin of Harbor."""
    try:
        user = cs.users.find(args.user)
    except exp.NotFound:
        print("User '%s' not found." % args.user)
    cs.users.set_admin(user['user_id'], False)
    print("Revoke admin privilege from user '%s' successfully." % args.user)


@utils.arg(
    'user',
    metavar='<user>',
    help='User name or id')
@utils.arg(
    '--email',
    metavar='<email>',
    dest='email',
    help='Email of the user')
@utils.arg(
    '--realname',
    metavar='<realname>',
    dest='realname',
    help='Email of the user')
@utils.arg(
    '--comment',
    metavar='<comment>',
    dest='comment',
    help='Comment of the user')
def do_user_update(cs, args):
    """Update a registered user to change his profile."""
    try:
        user = cs.users.find(args.user)
    except exp.NotFound:
        print("User '%s' not found." % args.user)
    realname = args.realname or user['realname']
    email = args.email or user['email']
    comment = args.comment or user['comment']
    cs.users.update(user['user_id'], realname, email, comment)
    user = cs.users.get(user['user_id'])
    utils.print_dict(user)


@utils.arg(
    'user',
    metavar='<user>',
    help='User name or id')
def do_change_password(cs, args):
    """Change the password on a user that already exists."""
    try:
        user = cs.users.find(args.user)
    except exp.NotFound:
        print("User '%s' not found." % args.user)
    old_password = getpass.getpass('Old password: ')
    new_password = getpass.getpass('New Password: ')
    try:
        cs.users.change_password(user['user_id'], old_password, new_password)
        print("Update password successfully.")
    except exp.Forbidden as e:
        print(e.message.replace("_", ' '))
        return 1


@utils.arg('user', metavar='<user>', help='ID or name of user.')
def do_user_show(cs, args):
    """Get a user's profile."""
    key = args.user
    if cs.users.is_id(key):
        id = key
    else:
        id = cs.users.get_id_by_name(key)
    user = cs.users.get(id)
    utils.print_dict(user)


@utils.arg(
    '--detail',
    '-d',
    dest="detail",
    action="store_true",
    help='show detail info.')
def do_whoami(cs, args):
    """Get current user info."""
    user = cs.users.current()
    if args.detail:
        utils.print_dict(user)
    else:
        print(user['username'])


@utils.arg(
    '--username',
    metavar='<username>',
    dest='username',
    required=True,
    help='Unique name of the new user')
@utils.arg(
    '--password',
    metavar='<password>',
    dest='password',
    required=True,
    help='Password of the new user')
@utils.arg(
    '--email',
    metavar='<email>',
    dest='email',
    required=True,
    help='Email of the new user')
@utils.arg(
    '--realname',
    metavar='<realname>',
    dest='realname',
    default=None,
    help='Email of the new user')
@utils.arg(
    '--comment',
    metavar='<comment>',
    dest='comment',
    default=None,
    help='Comment of the new user')
def do_user_create(cs, args):
    """Creates a new user account."""
    cs.users.create(args.username, args.password,
                    args.email, args.realname,
                    args.comment)
    print("Create user '%s' successfully." % args.username)


@utils.arg('user', metavar='<user>', help='ID or name of user.')
def do_user_delete(cs, args):
    """Mark a registered user as be removed."""
    key = args.user
    if cs.users.is_id(key):
        id = key
    else:
        id = cs.users.get_id_by_name(key)
    cs.users.delete(id)
    print("Delete user '%s' sucessfully." % key)


@utils.arg(
    '--sortby',
    metavar='<sortby>',
    dest="sortby",
    default="project_id",
    help='Sort key.')
def do_project_list(cs, args):
    """List projects."""
    projects = cs.projects.list()
    fields = [
        'project_id',
        'name',
        'owner_id',
        'current_user_role_id',
        'repo_count',
        'creation_time',
        'public',
    ]
    utils.print_list(projects, fields, formatters={}, sortby=args.sortby)


@utils.arg(
    '--project-id',
    '-p',
    dest='project_id',
    metavar='<project_id>',
    default=None,
    help='ID of project.')
def do_member_list(cs, args):
    """List a project's relevant role members."""
    project = args.project_id
    if not project:
        project = cs.client.project
    members = cs.projects.get_members(project)
    fields = [
        'username',
        'role_name',
        'user_id',
        'role_id',
    ]
    utils.print_list(members, fields, formatters={}, sortby='user_id')


@utils.arg('project', metavar='<project>', help='ID or name of project.')
def do_project_show(cs, args):
    """Show specific project detail infomation."""
    key = args.project
    if cs.projects.is_id(key):
        project_id = key
    else:
        project_id = cs.projects.get_id_by_name(key)
    projects = cs.projects.list()
    for project in projects:
        if str(project['project_id']) == str(project_id):
            utils.print_dict(project)
            return
    raise exp.NotFound("Project '%s' not found" % args.project)


@utils.arg('project', metavar='<project>', help='ID or name of project.')
def do_project_delete(cs, args):
    """Delete project by Id or name."""
    key = args.project
    if cs.projects.is_id(key):
        id = key
    else:
        try:
            id = cs.projects.get_id_by_name(key)
        except exp.NotFound:
            print("Project '%s' not found." % args.project)
            return 1
    try:
        cs.projects.delete(id)
        print("Delete Project '%s' successfully." % key)
        return 0
    except exp.NotFound:
        print("Project '%s' not Found." % args.project)
        return 1


@utils.arg(
    'name',
    metavar='<name>',
    help='Name of new project.')
@utils.arg(
    '--is-public',
    metavar='<is-public>',
    default=True,
    help='Make project accessible to the public (default true).')
def do_project_create(cs, args):
    """Create a new project."""
    is_public = strutils.bool_from_string(args.is_public, strict=True)
    try:
        cs.projects.create(args.name, is_public)
        print("Create project '%s' successfully." % args.name)
    except exp.Conflict:
        print("Project name '%s' already exists." % args.name)


@utils.arg(
    '--project-id',
    '-p',
    dest='project_id',
    metavar='<project_id>',
    default=None,
    help='ID of project.')
@utils.arg(
    '--sortby',
    dest='sortby',
    metavar='<sortby>',
    default='Id',
    help='Sort key.')
def do_list(cs, args):
    """Get repositories accompany with relevant project and repo name."""
    pros = cs.repositories.list_projects()
    for pro in pros:
        repositories = cs.repositories.list(pro['name'])
        data = []
        for repo in repositories:
            tags = cs.repositories.list_tags(repo['name'])['tags']
            for tag in tags:
                item = repo.copy()
                manifest = cs.repositories.get_manifests(item['name'], tag)
                size = 0

                for layer in manifest['layers']:
                    size += layer['size']
                item['size'] = size

                if tag != 'latest':
                    item['name'] = repo['name'] + ":" + tag
                data.append(item)
        fields = [
            "name", 'project_id', 'size',
            "tags_count", "star_count", "pull_count",
            "update_time"
        ]
        print('=' * 20, 'Project(%s) info' % pro['name'], '=' * 20)
        utils.print_list(data, fields, sortby=args.sortby)


@utils.arg(
    'repository',
    metavar='<repository>',
    help='Regular Expression of repository to be deleted.')
@utils.arg(
    '--dry-run',
    '-d',
    dest='dryrun',
    action="store_true",
    help="will only print what would have been deleted")
def do_repository_delete(cs, args):
    """Delete repository"""
    # list all the repositories to delete
    repositories = cs.repositories.list(cs.client.project)
    for repo in repositories:
        if re.match(args.repository, repo['name']):
            if args.dryrun:
                print("Would have deleted : %s" % repo['name'])
            else:
                cs.repositories.delete_repository(repo['name'])
                print("Repository %s deleted" % repo['name'])


@utils.arg('repository', metavar='<repository>', help='Name of repository.')
def do_tags_list(cs, args):
    """Get tags of a relevant repository."""
    tags = cs.repositories.list_tags(args.repository)
    fields = ["name", 'author', 'architecture',
              'os', 'docker_version', 'created']
    utils.print_list(tags, fields, sortby="name")


@utils.arg('repository', metavar='<repository>', help='Name of repository.')
@utils.arg('tag', metavar='<tag>', help='Name of the tag.')
def do_tags_delete(cs, args):
    """delete tag of a relevant repository."""
    try:
        rc = cs.repositories.delete_tags(args.repository, args.tag)
        print("Delete tag '%s:%s' sucessfully with return code %s" %
              (args.repository, args.tag, rc))
    except exp.NotFound as e:
        print("%s:%s not found : %s" % (args.repository, args.tag, e.message))


@utils.arg(
    '--repository',
    '-r',
    dest='repository',
    help='repository regular expression')
@utils.arg(
    '--tag',
    '-t',
    dest='tag',
    help='tag regular expression.')
@utils.arg(
    '--dry-run',
    '-d',
    dest='dryrun',
    action="store_true",
    help="will only print what would have been removed")
def do_tags_delete_reg(cs, args):
    """delete all tags that matches the expression of a relevant repository."""
    # List the repositories and keep the maching ones
    repositories = cs.repositories.list(cs.client.project)
    matching_repositories = []
    for repository in repositories:
        if re.match(args.repository, repository['name']):
            print("Found repository : %s" % repository['name'])
            matching_repositories.append(repository['name'])
    # List the tags and keep the matching ones
    for repository in matching_repositories:
        tags = cs.repositories.list_tags(repository)

        for tag in tags:
            if re.match(args.tag, tag['name']):
                if args.dryrun:
                    print("Would have removed : %s:%s" %
                          (repository, tag['name']))
                else:
                    cs.repositories.delete_tags(repository, tag['name'])
                    print("Removed : %s:%s" % (repository, tag['name']))


@utils.arg(
    '--project-id',
    '-p',
    dest='project_id',
    metavar='<project_id>',
    default=None,
    help='ID of project.')
@utils.arg(
    'repository',
    metavar='<repository>',
    help="Repository name, for example: int32bit/ubuntu:14.04.")
def do_show(cs, args):
    """Show specific repository detail infomation."""

    repo = args.repository
    tag_index = repo.find(':')
    tag = ''
    if tag_index != -1:
        tag = repo[tag_index + 1:]
        repo = repo[:tag_index]
    if repo.find('/') == -1:
        repo = "library/" + repo
    pros = cs.repositories.list_projects()
    for pro in pros:
        repos = cs.repositories.list(pro['name'])
        found_repo = None
        for r in repos:
            if r['name'] == repo:
                found_repo = r
                break
        if not found_repo:
            continue

        if not tag:
            tags = cs.repositories.list_tags(found_repo['name'])['tags']
            found_repo['tags'] = tags
            utils.print_dict(found_repo)
        else:
            found_repo['tag'] = tag
            utils.print_dict(found_repo)
        break


@utils.arg(
    '--count',
    '-c',
    metavar='<count>',
    dest='count',
    default=5,
    help='Count.')
def do_top(cs, args):
    """Get public repositories which are accessed most."""
    try:
        count = int(args.count)
    except ValueError:
        print("'%s' is not a valid number." % args.count)
        return 1
    if count < 1:
        print("invalid count %s, count must > 0." % args.count)
        return 1
    data = cs.repositories.get_top(count)
    utils.print_list(data,
                     ['name', 'pull_count', 'star_count'],
                     sortby='pull_count')


@utils.arg(
    'query',
    metavar='<query>',
    help='Search parameter for project and repository name.')
def do_search(cs, args):
    """Search for projects and repositories."""
    data = cs.searcher.search(args.query)
    project_fields = ['project_id', 'name', 'public',
                      'repo_count', 'creation_time']
    print("Find %d Projects: " % len(data['project']))
    utils.print_list(
        data['project'], project_fields, formatters={}, sortby='id')
    repository_fields = [
        'repository_name', 'project_name', 'project_id', 'project_public'
    ]
    print("\n")
    print("Find %d Repositories: " % len(data['repository']))
    utils.print_list(
        data['repository'],
        repository_fields,
        formatters={},
        sortby='repository_name')


def do_usage(cs, args):
    """Get projects number and repositories number relevant to the user."""
    data = cs.statistics.list()
    utils.print_dict(data)


@utils.arg(
    '--sortby',
    dest='sortby',
    metavar='<sortby>',
    default='op_time',
    help='Sort key.')
def do_logs(cs, args):
    """Get recent logs of the projects which the user is a member of."""
    pros = cs.repositories.list_projects()
    for pro in pros:
        try:
            logs = cs.logs.list(pro['name'])
        except harborclient.exceptions.Forbidden:
            logs = [{}]
        print('=' * 20, 'Project %s logs' % pro['name'], '=' * 20)
        fields = ['id', 'op_time', 'username',
                  'resource', 'operation', 'resource_type']
        utils.print_list(logs, fields, sortby=args.sortby)


def do_info(cs, args):
    """Get general system info."""
    info = cs.systeminfo.get()
    try:
        volumes = cs.systeminfo.get_volumes()
        info['disk_total'] = volumes['storage'][0]['total']
        info['disk_free'] = volumes['storage'][0]['free']
    except exp.Forbidden:
        # Only admin can get volumes
        pass
    utils.print_dict(info)


def do_get_cert(cs, args):
    """Get default root cert under OVA deployment."""
    try:
        certs = cs.systeminfo.get_cert()
        print(certs)
    except exp.NotFound:
        print("No certificate found")
    except exp.Forbidden:
        print("Only admin can perform this operation.")


def do_version(cs, args):
    """Get harbor version."""
    info = cs.systeminfo.get()
    print(info['harbor_version'])


def do_get_conf(cs, args):
    """Get system configurations."""
    try:
        configurations = cs.configurations.get()
    except exp.Forbidden:
        raise exp.CommandError("Only admin can perform this operation.")
    data = []
    for key in configurations:
        item = {}
        item['name'] = key
        item['value'] = configurations[key].get('value')
        item['editable'] = configurations[key].get('editable')
        data.append(item)
    utils.print_list(data, ['name', 'value', 'editable'], sortby='name')


@utils.arg(
    'target',
    metavar='<target>',
    help="The target name or id.")
def do_policy_list(cs, args):
    """List filters policies by name and project_id."""
    target = None
    if is_id(args.target):
        target = args.target
    else:
        targets = cs.targets.list()
        for t in targets:
            if t['name'] == args.target:
                target = t['id']
                break
    if not target:
        print("target '%s' not found!" % args.target)
        return 1
    try:
        policies = cs.targets.list_policies(target)
    except exp.NotFound:
        print("target '%s' not found!" % args.target)
        return 1
    if not policies:
        policies = []
    fields = ["id", "name", "description",
              "enabled", "start_time", "cron_str",
              "creation_time"]
    utils.print_list(policies, fields, sortby='id')
