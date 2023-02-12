# machine_learning_systems

This repository is a guide to building Machine Learning systems.

## Understand the problem and establish scope

### functional requirements (i.e. features):

Our objective is to help users sift through a wide variety of user reviews for a given set of products in real-time using natural language. A typical user is interested in two particular features:

1. Document retrieval/filtering based on NLP rather than filtering based on stars. (e.g. what are users saying about the battery life of a phone --> show review X)
2. Users can require a summary of what users have to say about a product using content generation (e.g. Summarize the top N reviews)
3. Users can provide feedback on the summary to improve the quality of the summary.

### non functional requirements:

- Scalability:
  - Queries Per Second: Should be able to handle 10.000 QPS.
- Availability:
  - Systems should have X-Nines of availability.
- Freshness:
  - New product reviews should be available within one day of submitting.
  - ML Models should be retrained (and potentially redeployed) on a daily basis.
  -

## Propose high-level design and get buy-in

- High level API design:

| API                   | Details                                                          |
| --------------------- | ---------------------------------------------------------------- |
| GET /reviews/         | Get all reviews                                                  |
| GET /reviews/:id      | Get a review by ID                                               |
| POST /search          | Filter/Search for documents based on a query                     |
| POST /search/feedback | Provide BOOLEAN feedback on the search results (relevant or not) |
| POST /search/summary  | Generate a summary of the top N documents                        |
| --------------------- | ---------------------------------------------------------------- |

- High level architecture:
