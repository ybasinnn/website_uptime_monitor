"""Generates images/website_monitor_architecture.png.

Usage (from the repo root, requires Graphviz):
    pip install diagrams
    python docs/architecture/architecture.py
"""

from diagrams import Cluster, Diagram, Edge
from diagrams.aws.compute import Lambda
from diagrams.aws.database import Dynamodb
from diagrams.aws.integration import Eventbridge, SNS
from diagrams.aws.management import Cloudwatch
from diagrams.aws.network import APIGateway
from diagrams.aws.storage import S3
from diagrams.onprem.ci import GithubActions
from diagrams.onprem.client import User
from diagrams.onprem.iac import Terraform
from diagrams.onprem.network import Internet
from diagrams.aws.engagement import SimpleEmailServiceSesEmail

GRAPH_ATTR = {
    "fontsize": "22",
    "fontname": "Helvetica",
    "pad": "0.6",
    "nodesep": "0.7",
    "ranksep": "1.4",
    "splines": "spline",
    "bgcolor": "white",
}
NODE_ATTR = {"fontname": "Helvetica", "fontsize": "13"}
EDGE_ATTR = {"fontname": "Helvetica", "fontsize": "11", "color": "#545B64"}

CLUSTER_AWS = {"bgcolor": "#F7F9FB", "pencolor": "#232F3E", "fontsize": "15", "fontname": "Helvetica-Bold"}
CLUSTER_MON = {"bgcolor": "#EAF4FF", "pencolor": "#5A8DD6", "fontsize": "13", "fontname": "Helvetica-Bold"}
CLUSTER_DASH = {"bgcolor": "#EDF8EE", "pencolor": "#4F9A57", "fontsize": "13", "fontname": "Helvetica-Bold"}
CLUSTER_CICD = {"bgcolor": "#F4F0FB", "pencolor": "#7B42BC", "fontsize": "13", "fontname": "Helvetica-Bold"}

DATA = {"color": "#1F6FEB", "penwidth": "1.6"}
ALERT = {"color": "#D13212", "penwidth": "1.6"}
DEPLOY = {"color": "#7B42BC", "style": "dashed", "penwidth": "1.4"}
LOGS = {"color": "#8A939D", "style": "dotted"}

with Diagram(
    "Serverless Website Uptime Monitor",
    filename="images/website_monitor_architecture",
    outformat="png",
    show=False,
    direction="LR",
    graph_attr=GRAPH_ATTR,
    node_attr=NODE_ATTR,
    edge_attr=EDGE_ATTR,
):
    with Cluster("CI/CD", graph_attr=CLUSTER_CICD):
        gha = GithubActions("GitHub Actions\nplan on PR · apply on main\nmanual apply / destroy")
        tfc = Terraform("HCP Terraform\nworkspace")
        gha >> Edge(label="create run", **DEPLOY) >> tfc

    user = User("Visitor")
    target = Internet("Target website\n(var.target_url)")
    inbox = SimpleEmailServiceSesEmail("Email\nsubscriber")

    with Cluster("AWS account", graph_attr=CLUSTER_AWS):
        logs = Cloudwatch("CloudWatch Logs")

        with Cluster("Monitoring", graph_attr=CLUSTER_MON):
            schedule = Eventbridge("EventBridge\nrate(5 minutes)")
            checker = Lambda("Health-check Lambda\nPython 3.11")
            table = Dynamodb("DynamoDB\nresults (on-demand)")
            topic = SNS("SNS topic\nalerts")

        with Cluster("Dashboard", graph_attr=CLUSTER_DASH):
            bucket = S3("S3 static website\nindex.html")
            api = APIGateway("API Gateway (HTTP)\nGET /results")
            fetcher = Lambda("Dashboard Lambda\nPython 3.11")

    # Monitoring flow
    schedule >> Edge(label="invoke", **DATA) >> checker
    checker >> Edge(label="HTTPS GET + TLS/cert check", **DATA) >> target
    checker >> Edge(label="PutItem", **DATA) >> table
    checker >> Edge(label="publish on failure", **ALERT) >> topic
    topic >> Edge(label="email", **ALERT) >> inbox

    # Dashboard flow: the browser loads the page from S3, then calls the API itself
    user >> Edge(label="1. load page", **DATA) >> bucket
    user >> Edge(label="2. fetch results", **DATA) >> api
    api >> Edge(label="proxy", **DATA) >> fetcher
    fetcher >> Edge(label="read latest", **DATA) >> table

    # Cross-cutting
    [checker, fetcher] >> Edge(**LOGS) >> logs

    # Deployment
    tfc >> Edge(label="provisions all resources", **DEPLOY) >> schedule
